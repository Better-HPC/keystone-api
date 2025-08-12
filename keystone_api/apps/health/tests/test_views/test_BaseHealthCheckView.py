"""Unit tests for the `BaseHealthCheckView` class."""

from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from apps.health.views import BaseHealthCheckView


class ConcreteHealthCheckView(BaseHealthCheckView):
    """Concrete implementation of the abstract `BaseHealthCheckView` class."""

    @staticmethod
    def render_response(plugins: dict) -> HttpResponse:
        return HttpResponse("OK", status=200)


@patch.object(BaseHealthCheckView, 'check')
class GetMethod(TestCase):
    """Test the handling of `GET` requests via the `get` method."""

    def setUp(self) -> None:
        """Clear any cached request/response data before running tests."""

        cache.delete(BaseHealthCheckView._cache_key)

    def test_status_checks_are_run(self, mock_check: Mock) -> None:
        """Verify status checks are updated when processing get requests"""

        request = HttpRequest()
        view = ConcreteHealthCheckView()
        view.get(request)

        # Test the method for updating health checks was run
        mock_check.assert_called_once()

    def test_response_is_cached_after_get(self, mock_check: Mock) -> None:
        """Verify response is cached after processing get requests."""

        request = HttpRequest()
        view = ConcreteHealthCheckView()
        response = view.get(request)

        # Response should now be cached
        cached_response = cache.get(BaseHealthCheckView._cache_key)
        self.assertIsNotNone(cached_response)
        self.assertEqual(response.status_code, cached_response.status_code)
        self.assertEqual(response.content, cached_response.content)

    def test_cached_response_is_returned_without_check(self, mock_check: Mock) -> None:
        """Verify the cached response is returned when available and `check` is NOT called"""

        request = HttpRequest()
        view = ConcreteHealthCheckView()

        # Create and cache a fake HttpResponse
        fake_response = HttpResponse("cached content")
        cache.set(BaseHealthCheckView._cache_key, fake_response, 60)

        response = view.get(request)

        mock_check.assert_not_called()
        self.assertEqual(fake_response.status_code, response.status_code)
        self.assertEqual(fake_response.content, response.content)
