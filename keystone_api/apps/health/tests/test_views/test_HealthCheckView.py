"""Unit tests for the `HealthCheckView` class."""

from django.test import TestCase

from apps.health.tests.test_views.utils import create_mock_plugin
from apps.health.views import HealthCheckView


class RenderResponseMethod(TestCase):
    """Tests the `render_response` method correctly returns the health check status."""

    def test_failing_health_checks(self) -> None:
        """Verify the returned status code is 500 when some health checks are failing."""

        health_checks = {
            'plugin1': create_mock_plugin(1, 'OK', True),
            'plugin2': create_mock_plugin(0, 'Error', False)
        }

        response = HealthCheckView.render_response(health_checks)
        self.assertEqual(response.status_code, 500)

    def test_passing_health_checks(self) -> None:
        """Verify the returned status code is 200 when all health checks are passing."""

        health_checks = {
            'plugin1': create_mock_plugin(1, 'OK', True),
            'plugin2': create_mock_plugin(1, 'OK', False)
        }

        response = HealthCheckView.render_response(health_checks)
        self.assertEqual(response.status_code, 200)
