"""Unit tests for the `BaseHealthCheckView` class."""

from unittest.mock import patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.health.views import BaseHealthCheckView, CACHE_TIMEOUT

HEALTH_CHECK_CACHE_KEY = 'healthcheck_results'

MOCK_RESULTS = [
    {"check": "Database", "healthy": True, "error": None, "time_taken": 0.01},
]


class ConcreteHealthCheckView(BaseHealthCheckView):
    """Concrete implementation of the abstract `BaseHealthCheckView` class."""

    def render_response(self, results: list[dict]) -> HttpResponse:
        return HttpResponse("OK", status=200)


class GetMethod(TestCase):
    """Test the handling of `GET` requests by the `get` method."""

    def setUp(self) -> None:
        """Clear the health check cache before each test."""

        cache.delete(HEALTH_CHECK_CACHE_KEY)
        self.view = ConcreteHealthCheckView()

    def test_checks_are_run_on_cache_miss(self) -> None:
        """Verify health checks are executed when the cache is cold."""

        request = Request(RequestFactory().get('/'))
        with patch.object(BaseHealthCheckView, 'get_cached_results', return_value=MOCK_RESULTS) as mock_get:
            self.view.get(request)
            mock_get.assert_called_once()

    def test_results_are_cached_after_request(self) -> None:
        """Verify health check results are stored in the cache after a GET request."""

        request = Request(RequestFactory().get('/'))
        with patch('apps.health.views.async_to_sync') as mock_sync:
            mock_sync.return_value = lambda _: MOCK_RESULTS
            self.view.get(request)

        cached = cache.get('healthcheck_results')
        self.assertIsNotNone(cached)
        self.assertEqual(cached, MOCK_RESULTS)

    def test_cached_results_skip_checks(self) -> None:
        """Verify cached results are returned without re-running health checks."""

        cache.set('healthcheck_results', MOCK_RESULTS, CACHE_TIMEOUT)

        request = Request(RequestFactory().get('/'))
        with patch.object(BaseHealthCheckView, 'run_checks') as mock_run:
            self.view.get(request)
            mock_run.assert_not_called()

    def test_render_response_receives_results(self) -> None:
        """Verify `render_response` is called with the results from `get_cached_results`."""

        request = Request(RequestFactory().get('/'))
        with patch.object(BaseHealthCheckView, 'get_cached_results', return_value=MOCK_RESULTS):
            with patch.object(self.view, 'render_response', return_value=HttpResponse()) as mock_render:
                self.view.get(request)
                mock_render.assert_called_once_with(MOCK_RESULTS)
