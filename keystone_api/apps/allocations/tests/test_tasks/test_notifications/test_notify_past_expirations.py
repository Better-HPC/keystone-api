"""Unit tests for the `notify_past_expirations` function."""

from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from apps.allocations.tasks import notify_past_expirations


class NotifyPastExpirationsMethod(TestCase):
    """Test the reporting of task failure."""

    @patch('apps.allocations.tasks.should_notify_past_expiration')
    @patch('apps.allocations.models.AllocationRequest.objects.filter')
    def test_raises_error_on_failure(self, mock_filter: Mock, mock_should_notify: Mock) -> None:
        """Verify a `RuntimeError` is raised when one or more notifications fail.

        Raising an error on failure is required to ensure Celery tasks
        report the correct status on exit.
        """

        mock_user = MagicMock()
        mock_request = MagicMock()
        mock_request.team.get_all_members.return_value.filter.return_value = [mock_user]
        mock_filter.return_value.all.return_value = [mock_request]

        mock_should_notify.side_effect = Exception("Test error")
        with self.assertRaisesRegex(RuntimeError, 'Task failed with one or more errors.*'):
            notify_past_expirations()
