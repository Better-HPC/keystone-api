"""Tests for the `HealthCheckPrometheusView` class."""

from django.test import TestCase

from apps.health.tests.views.utils import create_mock_plugin
from apps.health.views import HealthCheckPrometheusView


class RenderResponse(TestCase):
    """Tests for the `render_response` function"""

    def test_return_matches_health_checks(self) -> None:
        """Test the rendering of application health checks in Prometheus format"""

        health_checks = {
            'plugin1': create_mock_plugin(1, 'OK', True),
            'plugin2': create_mock_plugin(0, 'Error', False)
        }

        expected_response = '\n'.join([
            'plugin1{critical_service="True",message="OK"} 200.0',
            'plugin2{critical_service="False",message="Error"} 500.0'
        ])

        response = HealthCheckPrometheusView.render_response(health_checks)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_response, response.content.decode())
