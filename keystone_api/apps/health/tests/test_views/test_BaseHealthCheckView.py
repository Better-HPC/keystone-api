"""Unit tests for the `BaseHealthCheckView` class."""

from unittest.mock import Mock, patch

from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from apps.health.views import BaseHealthCheckView


class ConcreteHealthCheckView(BaseHealthCheckView):
    """Concrete implementation of the abstract `BaseHealthCheckView` class."""

    @staticmethod
    def render_response(plugins: dict) -> HttpResponse:
        return HttpResponse("OK", status=200)


class GetMethod(TestCase):
    """Test the handling of `GET` requests via the `get` method."""

    @patch.object(BaseHealthCheckView, 'check')
    def test_status_checks_are_run(self, mock_check: Mock) -> None:
        """Verify status checks are updated when processing get requests"""

        request = HttpRequest()
        view = ConcreteHealthCheckView()
        view.get(request)

        # Test the method for updating health checks was run
        mock_check.assert_called_once()
