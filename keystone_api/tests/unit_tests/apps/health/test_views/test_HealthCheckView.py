"""Unit tests for the `HealthCheckView` class."""

from django.test import TestCase

from apps.health.views import HealthCheckView


class RenderResponseMethod(TestCase):
    """Test the rendering of HTTP responses by the `render_response` method."""

    def test_partial_failing_health_checks_returns_500(self) -> None:
        """Verify a 500 is returned when at least one health check is failing."""

        results = [
            {"check": "Database", "healthy": True, "error": None, "time_taken": 0.01},
            {"check": "Redis", "healthy": False, "error": "Connection refused", "time_taken": 1.0},
        ]

        response = HealthCheckView().render_response(results)
        self.assertEqual(response.status_code, 500)

    def test_all_failing_health_checks_returns_500(self) -> None:
        """Verify a 500 is returned when all health checks are failing."""

        results = [
            {"check": "Database", "healthy": False, "error": "DB unavailable", "time_taken": 0.5},
            {"check": "Redis", "healthy": False, "error": "Connection refused", "time_taken": 1.0},
        ]

        response = HealthCheckView().render_response(results)
        self.assertEqual(response.status_code, 500)

    def test_passing_health_checks_returns_200(self) -> None:
        """Verify a 200 is returned when all health checks are passing."""

        results = [
            {"check": "Database", "healthy": True, "error": None, "time_taken": 0.01},
            {"check": "Redis", "healthy": True, "error": None, "time_taken": 0.02},
        ]

        response = HealthCheckView().render_response(results)
        self.assertEqual(response.status_code, 200)

    def test_empty_results_returns_200(self) -> None:
        """Verify a 200 is returned when there are no health checks."""

        response = HealthCheckView().render_response([])
        self.assertEqual(response.status_code, 200)
