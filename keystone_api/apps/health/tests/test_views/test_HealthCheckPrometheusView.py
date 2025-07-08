"""Unit tests for the `HealthCheckPrometheusView` class."""

from django.test import TestCase

from apps.health.tests.test_views.utils import create_mock_plugin
from apps.health.views import HealthCheckPrometheusView


class RenderResponseMethod(TestCase):
    """Test the `render_response` method correctly returns the health check status."""

    def test_return_matches_health_checks(self) -> None:
        """Verify health checks are correctly rendered in Prometheus format."""

        health_checks = {
            'plugin1': create_mock_plugin(1, 'OK', True),
            'plugin2': create_mock_plugin(0, 'Error', False)
        }

        expected_response = (
            '# HELP plugin1 unittest.mockMagicMock\n'
            '# TYPE plugin1 gauge\n'
            'plugin1{critical_service="True",message="OK"} 200.0\n'
            '\n'
            '# HELP plugin2 unittest.mockMagicMock\n'
            '# TYPE plugin2 gauge\n'
            'plugin2{critical_service="False",message="Error"} 500.0'
        )

        response = HealthCheckPrometheusView().render_response(health_checks)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_response, response.content.decode())


class SanitizeMetricNameMethod(TestCase):
    """Test metric name sanitation via the `sanitize_metric_name` method."""

    def test_valid_name_remains_unchanged(self) -> None:
        """Verify valid metric names remain unchanged."""

        self.assertEqual(
            'valid_metric_name',
            HealthCheckPrometheusView.sanitize_metric_name('valid_metric_name')
        )

    def test_replaces_invalid_chars_with_underscore(self) -> None:
        """Verify invalid characters are be replaced with underscores."""

        self.assertEqual(
            'metric_name_',
            HealthCheckPrometheusView.sanitize_metric_name('metric[name]')
        )

        self.assertEqual(
            'DatabaseBackend_default_',
            HealthCheckPrometheusView.sanitize_metric_name('DatabaseBackend[default]')
        )

    def test_starts_with_invalid_char(self) -> None:
        """Verify metric starting with invalid characters are prefixed."""

        self.assertEqual(
            '_1metric',
            HealthCheckPrometheusView.sanitize_metric_name('1metric'),
        )

    def test_empty_string(self) -> None:
        """Verify an empty input returns a valid metric."""

        self.assertEqual(
            '_',
            HealthCheckPrometheusView.sanitize_metric_name('')
        )

    def test_complex_case(self) -> None:
        """Verify sanitation of a complex, invalid name."""

        self.assertEqual(
            HealthCheckPrometheusView.sanitize_metric_name('Some@Strange#Name!With$Chars'),
            'Some_Strange_Name_With_Chars'
        )
