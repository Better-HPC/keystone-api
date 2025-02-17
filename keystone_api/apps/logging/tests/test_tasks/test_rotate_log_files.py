"""Unit tests for the `rotate_log_files` task."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import override_settings, TestCase
from django.utils.timezone import now

from apps.logging.models import AppLog, RequestLog
from apps.logging.tasks import clear_log_files


class ClearLogFilesMethod(TestCase):
    """Test the deletion of log records by the  clear_log_files` method."""

    def create_dummy_records(self, timestamp: datetime) -> None:
        """Create a single record in each logging database table.

        Args:
            timestamp: The creation time of the records.
        """

        AppLog.objects.create(
            name='mock.log.test',
            level=10,
            pathname='/test',
            lineno=100,
            message='This is a log',
            time=timestamp
        )

        RequestLog.objects.create(
            endpoint='/api',
            response_code=200,
            time=timestamp
        )

    @override_settings(CONFIG_LOG_RETENTION=4)
    @override_settings(CONFIG_REQUEST_RETENTION=4)
    @patch('django.utils.timezone.now')
    def test_log_files_deleted(self, mock_now: Mock) -> None:
        """Verify expired log files are deleted."""

        # Mock the current time
        initial_time = now()
        mock_now.return_value = initial_time

        # Create an older set of records
        self.create_dummy_records(timestamp=initial_time)

        # Simulate the passage of time
        later_time = initial_time + timedelta(seconds=5)
        mock_now.return_value = later_time

        # Create a newer set of records
        self.create_dummy_records(timestamp=later_time)

        # Ensure records exist
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())

        # Run rotation
        clear_log_files()

        # Assert only the newer records remain
        self.assertEqual(1, AppLog.objects.count())
        self.assertEqual(1, RequestLog.objects.count())

    @override_settings(CONFIG_LOG_RETENTION=0)
    @override_settings(CONFIG_REQUEST_RETENTION=0)
    def test_deletion_disabled(self) -> None:
        """Verify log files are not deleted when log clearing is disabled."""

        self.create_dummy_records(now())

        clear_log_files()
        self.assertEqual(1, AppLog.objects.count())
        self.assertEqual(1, RequestLog.objects.count())
