"""Unit tests for the `HealthCheckPrometheusView` class."""

from django.test import TestCase

from apps.health.views import HealthCheckPrometheusView


class RenderResponseMethod(TestCase):
    """Test the rendering of HTTP responses by the `render_response` method."""

    def test_status_code_is_always_200(self) -> None:
        """Verify the status code is 200 regardless of individual health check results."""

        results = [
            {"check": "Database", "healthy": False, "error": "DB unavailable", "time_taken": 0.5},
        ]

        response = HealthCheckPrometheusView().render_response(results)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_plain_text(self) -> None:
        """Verify the response uses the Prometheus plain-text content type."""

        response = HealthCheckPrometheusView().render_response([])
        self.assertIn("text/plain", response.headers.get("Content-Type", ""))

    def test_status_metric_block_is_present(self) -> None:
        """Verify the HELP and TYPE lines for the status metric are present."""

        response = HealthCheckPrometheusView().render_response([])
        body = response.content.decode()

        self.assertIn("# HELP keystone_health_check_status", body)
        self.assertIn("# TYPE keystone_health_check_status gauge", body)

    def test_timing_metric_block_is_present(self) -> None:
        """Verify the HELP and TYPE lines for the timing metric are present."""

        response = HealthCheckPrometheusView().render_response([])
        body = response.content.decode()

        self.assertIn("# HELP keystone_health_check_eval_time_seconds", body)
        self.assertIn("# TYPE keystone_health_check_eval_time_seconds gauge", body)

    def test_healthy_check_emits_correct_status_value(self) -> None:
        """Verify a passing check emits a truthy status value (1)."""

        results = [{"check": "Storage", "healthy": True, "error": None, "time_taken": 0.008}]
        response = HealthCheckPrometheusView().render_response(results)
        body = response.content.decode()

        self.assertIn('keystone_health_check_status{check="Storage"} 1', body)

    def test_unhealthy_check_emits_correct_status_value(self) -> None:
        """Verify a failing check emits a falsy status value (0)."""

        results = [{"check": "Celery", "healthy": False, "error": "Workers unavailable", "time_taken": 1.001}]
        response = HealthCheckPrometheusView().render_response(results)
        body = response.content.decode()

        self.assertIn('keystone_health_check_status{check="Celery"} 0', body)

    def test_timing_metric_uses_six_decimal_places(self) -> None:
        """Verify timing values are formatted to six decimal places."""

        results = [{"check": "Storage", "healthy": True, "error": None, "time_taken": 0.008}]
        response = HealthCheckPrometheusView().render_response(results)
        body = response.content.decode()

        self.assertIn('keystone_health_check_eval_time_seconds{check="Storage"} 0.008000', body)

    def test_multiple_checks_all_appear(self) -> None:
        """Verify all checks are represented in the output."""

        results = [
            {"check": "Storage", "healthy": True, "error": None, "time_taken": 0.012},
            {"check": "Celery", "healthy": False, "error": "Workers unavailable", "time_taken": 1.001},
        ]

        response = HealthCheckPrometheusView().render_response(results)
        body = response.content.decode()

        self.assertIn('check="Storage"', body)
        self.assertIn('check="Celery"', body)

    def test_full_output_format(self) -> None:
        """Verify the complete Prometheus output matches the expected format exactly."""

        results = [
            {"check": "Storage", "healthy": True, "error": None, "time_taken": 0.012},
            {"check": "Celery", "healthy": False, "error": "Workers unavailable", "time_taken": 1.001},
        ]

        expected = (
            "# HELP keystone_health_check_status Health check status (200 = healthy, 500 = unhealthy)\n"
            "# TYPE keystone_health_check_status gauge\n"
            'keystone_health_check_status{check="Storage"} 1\n'
            'keystone_health_check_status{check="Celery"} 0\n'
            "\n"
            "# HELP keystone_health_check_eval_time_seconds Health check evaluation time in seconds\n"
            "# TYPE keystone_health_check_eval_time_seconds gauge\n"
            'keystone_health_check_eval_time_seconds{check="Storage"} 0.012000\n'
            'keystone_health_check_eval_time_seconds{check="Celery"} 1.001000\n'
        )

        response = HealthCheckPrometheusView().render_response(results)
        self.assertEqual(response.content.decode(), expected)
