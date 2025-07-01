"""Unit tests for the `SMTPHealthCheck` class."""

from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from apps.health.backends import SMTPHealthCheck


class CheckStatusMethod(TestCase):
    """Unit tests for the validation of SMTP settings via the `check_status` method."""

    @patch("apps.health.backends.get_connection")
    def test_check_status_success(self, mock_get_connection: Mock) -> None:
        """Verify no errors are raised on a successful status check."""

        mock_connection = MagicMock()
        mock_connection.host = "smtp.example.com"
        mock_get_connection.return_value = mock_connection

        health_check = SMTPHealthCheck()
        health_check.check_status()

        mock_connection.open.assert_called_once()
        mock_connection.connection.noop.assert_called_once()

        self.assertEqual(len(health_check.errors), 0)

    @patch("apps.health.backends.get_connection")
    def test_check_status_improperly_configured(self, mock_get_connection: Mock) -> None:
        """Verify the health check fails when an SMTP backend is not configured."""

        mock_connection = MagicMock()
        mock_connection.host = None
        mock_get_connection.return_value = mock_connection

        health_check = SMTPHealthCheck()
        health_check.check_status()

        self.assertEqual(len(health_check.errors), 1)
        self.assertEqual("Email backend is not configured properly.", health_check.errors[0].message)

    @patch("apps.health.backends.get_connection")
    def test_check_status_connection_error(self, mock_get_connection: Mock) -> None:
        """Verify the health check fails when the SMTP server cannot be reached."""

        mock_connection = MagicMock()
        mock_connection.host = "smtp.example.com"
        mock_connection.open.side_effect = Exception("Connection failed")
        mock_get_connection.return_value = mock_connection

        health_check = SMTPHealthCheck()
        health_check.check_status()

        self.assertEqual(len(health_check.errors), 1)
        self.assertEqual("Connection failed", health_check.errors[0].message)
