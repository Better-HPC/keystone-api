"""Unit tests for the `rotate_log_files` task."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import override_settings, TestCase
from django.utils.timezone import now

from apps.logging.models import AppLog, AuditLog, RequestLog
from apps.logging.tasks import clear_log_files


class ClearLogFilesMethod(TestCase):
    """Test the deletion of log records by the  clear_log_files` method."""

    @staticmethod
    def create_dummy_records(timestamp: datetime) -> None:
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
            timestamp=timestamp
        )

        RequestLog.objects.create(
            endpoint='/api',
            response_code=200,
            timestamp=timestamp
        )

        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(RequestLog),
            object_pk=str(1),
            object_id=1,
            object_repr="dummy",
            serialized_data={"example_field": "example_value"},
            action=AuditLog.Action.CREATE,
            changes_text="Created dummy object",
            changes={"message": ["", "Audit log object"]},
            timestamp=timestamp,
        )

    @override_settings(CONFIG_LOG_RETENTION=4)
    @patch('django.utils.timezone.now')
    def test_app_log_rotation(self, mock_current_time: Mock) -> None:
        """Verify expired log files are deleted."""

        # Create pairs of newer and older log records
        initial_time = now()
        mock_current_time.return_value = initial_time
        self.create_dummy_records(timestamp=initial_time)

        later_time = initial_time + timedelta(seconds=5)
        mock_current_time.return_value = later_time
        self.create_dummy_records(timestamp=later_time)

        # Ensure records exist
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())
        self.assertEqual(2, AuditLog.objects.count())

        # Simulate the passage of time and run log rotation
        mock_current_time.return_value = later_time
        clear_log_files()

        # Verify only the newer records remain
        self.assertEqual(1, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())
        self.assertEqual(2, AuditLog.objects.count())

    @override_settings(CONFIG_REQUEST_RETENTION=4)
    @patch('django.utils.timezone.now')
    def test_request_log_rotation(self, mock_current_time: Mock) -> None:
        """Verify expired log files are deleted."""

        # Create pairs of newer and older log records
        initial_time = now()
        mock_current_time.return_value = initial_time
        self.create_dummy_records(timestamp=initial_time)

        later_time = initial_time + timedelta(seconds=5)
        mock_current_time.return_value = later_time
        self.create_dummy_records(timestamp=later_time)

        # Ensure records exist
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())
        self.assertEqual(2, AuditLog.objects.count())

        # Simulate the passage of time and run log rotation
        mock_current_time.return_value = later_time
        clear_log_files()

        # Verify only the newer records remain
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(1, RequestLog.objects.count())
        self.assertEqual(2, AuditLog.objects.count())

    @override_settings(CONFIG_AUDIT_RETENTION=4)
    @patch('django.utils.timezone.now')
    def test_audit_log_rotation(self, mock_current_time: Mock) -> None:
        """Verify expired log files are deleted."""

        # Create pairs of newer and older log records
        initial_time = now()
        mock_current_time.return_value = initial_time
        self.create_dummy_records(timestamp=initial_time)

        later_time = initial_time + timedelta(seconds=5)
        mock_current_time.return_value = later_time
        self.create_dummy_records(timestamp=later_time)

        # Ensure records exist
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())
        self.assertEqual(2, AuditLog.objects.count())

        # Simulate the passage of time and run log rotation
        mock_current_time.return_value = later_time
        clear_log_files()

        # Verify only the newer records remain
        self.assertEqual(2, AppLog.objects.count())
        self.assertEqual(2, RequestLog.objects.count())
        self.assertEqual(1, AuditLog.objects.count())

    @override_settings(CONFIG_LOG_RETENTION=0)
    @override_settings(CONFIG_REQUEST_RETENTION=0)
    def test_deletion_disabled(self) -> None:
        """Verify log files are not deleted when log clearing is disabled."""

        self.create_dummy_records(now() - + timedelta(hours=1))

        clear_log_files()
        self.assertEqual(1, AppLog.objects.count())
        self.assertEqual(1, RequestLog.objects.count())
        self.assertEqual(1, AuditLog.objects.count())
