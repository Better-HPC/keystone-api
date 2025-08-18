"""Unit tests for the `BaseHealthCheckView` class."""

from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.health.views import BaseHealthCheckView


class ConcreteHealthCheckView(BaseHealthCheckView):
    """Concrete implementation of the abstract `BaseHealthCheckView` class."""

    cache_key = "concrete_health_check_key"

    @staticmethod
    def render_response(plugins: dict) -> HttpResponse:
        return HttpResponse("OK", status=200)


@patch.object(BaseHealthCheckView, 'check')
class GetMethod(TestCase):
    """Test the handling of `GET` requests via the `get` method."""

    def setUp(self) -> None:
        """Clear any cached request/response data before running tests."""

        self.view = ConcreteHealthCheckView()
        cache.delete(self.view.cache_key)

    def test_status_checks_are_run(self, mock_check: Mock) -> None:
        """Verify status checks are updated when processing get requests"""

        request = Request(RequestFactory().get('/'))
        self.view.get(request)

        # Test the method for updating health checks was run
        mock_check.assert_called_once()

    def test_response_is_cached(self, mock_check: Mock) -> None:
        """Verify responses are cached after processing get requests."""

        request = Request(RequestFactory().get('/'))
        response = self.view.get(request)

        # Response should now be cached
        cached_response = cache.get(self.view.cache_key)
        self.assertIsNotNone(cached_response)
        self.assertEqual(response.status_code, cached_response.status_code)
        self.assertEqual(response.content, cached_response.content)

    def test_cached_response_skips_checks(self, mock_check: Mock) -> None:
        """Verify cached responses are returned instead of evaluating system checks."""

        request = Request(RequestFactory().get('/'))

        # Create and cache a fake HttpResponse
        fake_response = HttpResponse("cached content")
        cache.set(self.view.cache_key, fake_response, 60)

        response = self.view.get(request)

        mock_check.assert_not_called()
        self.assertEqual(fake_response.status_code, response.status_code)
        self.assertEqual(fake_response.content, response.content)

    def test_cache_on_500(self, mock_check: Mock) -> None:
        """Verify responses are cached even if they have a 500 status code."""

        class ErrorHealthCheckView(BaseHealthCheckView):
            """A mock system health check view that always fails."""

            cache_key = "error_health_check_key"

            @staticmethod
            def render_response(plugins: dict) -> HttpResponse:
                return HttpResponse("Internal Server Error", status=500)

        request = Request(RequestFactory().get('/'))
        view = ErrorHealthCheckView()

        # Verify the response has 500 code, otherwise this test has no meaning
        cache.delete(view.cache_key)
        response = view.get(request)
        self.assertEqual(response.status_code, 500)

        # Verify 5xx responses are cached
        cached_response = cache.get(view.cache_key)
        self.assertIsNotNone(cached_response)
        self.assertEqual(500, cached_response.status_code)
        self.assertEqual(response.content, cached_response.content)
