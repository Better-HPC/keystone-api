"""Unit tests for the `rotate_log_files` task."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings, TestCase

from apps.logging.models import AppLog, AuditLog, RequestLog
from apps.logging.tasks import clear_log_records


@patch('django.utils.timezone.now')
class ClearLogRecordsMethod(TestCase):
    """Test the deletion of log records."""

    now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    def assert_log_counts(self, *, app: int = None, request: int = None, audit: int = None) -> None:
        """Assert the given number of log records exist.

        Args:
            app: The number of expected application logs.
            request: The number of expected request logs.
            audit: The number of expected audit logs.
        """

        if app is not None:
            self.assertEqual(app, AppLog.objects.count())

        if request is not None:
            self.assertEqual(request, RequestLog.objects.count())

        if audit is not None:
            self.assertEqual(audit, AuditLog.objects.count())

    def create_dummy_records(self, mock_now: Mock, *timestamps: datetime) -> None:
        """Create a series of log records at the given timestamps.

        Creates an application, request, and audit log record for each of the given timestamps.

        Args:
            mock_now: Mocked function used to return the current datetime.
            timestamps: The timestamps to create log records for.
        """

        log_count = len(timestamps)
        content_type = ContentType.objects.get_for_model(RequestLog)

        for ts in timestamps:
            mock_now.return_value = ts
            AppLog.objects.create(
                name='mock.log.test',
                level=10,
                pathname='/test',
                lineno=100,
                message='This is a log',
                timestamp=ts
            )

            RequestLog.objects.create(
                endpoint='/api',
                response_code=200,
                timestamp=ts
            )

            AuditLog.objects.create(
                content_type=content_type,
                object_pk="1",
                object_id=1,
                object_repr="dummy",
                serialized_data={"example_field": "example_value"},
                action=AuditLog.Action.CREATE,
                changes_text="Created dummy object",
                changes={"message": ["", "Audit log object"]},
                timestamp=ts
            )

        self.assert_log_counts(app=log_count, request=log_count, audit=log_count)

    @override_settings(CONFIG_LOG_RETENTION=4)
    @override_settings(CONFIG_REQUEST_RETENTION=0)
    @override_settings(CONFIG_AUDIT_RETENTION=0)
    def test_app_log_rotation(self, mock_now: Mock) -> None:
        """Verify the `CONFIG_AUDIT_RETENTION` setting enables app log rotation."""

        later_time = self.now + timedelta(seconds=settings.CONFIG_LOG_RETENTION)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(app=1, request=2, audit=2)
        self.assertEqual(later_time, AppLog.objects.first().timestamp)

    @override_settings(CONFIG_LOG_RETENTION=0)
    @override_settings(CONFIG_REQUEST_RETENTION=4)
    @override_settings(CONFIG_AUDIT_RETENTION=0)
    def test_request_log_rotation(self, mock_now: Mock) -> None:
        """Verify the `CONFIG_AUDIT_RETENTION` setting enables request log rotation."""

        later_time = self.now + timedelta(seconds=settings.CONFIG_REQUEST_RETENTION)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(app=2, request=1, audit=2)
        self.assertEqual(later_time, RequestLog.objects.first().timestamp)

    @override_settings(CONFIG_LOG_RETENTION=0)
    @override_settings(CONFIG_REQUEST_RETENTION=0)
    @override_settings(CONFIG_AUDIT_RETENTION=4)
    def test_audit_log_rotation(self, mock_now: Mock) -> None:
        """Verify the `CONFIG_AUDIT_RETENTION` setting enables audit log rotation."""

        later_time = self.now + timedelta(seconds=settings.CONFIG_AUDIT_RETENTION)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(app=2, request=2, audit=1)
        self.assertEqual(later_time, AuditLog.objects.first().timestamp)

    @override_settings(CONFIG_LOG_RETENTION=0)
    @override_settings(CONFIG_REQUEST_RETENTION=0)
    @override_settings(CONFIG_AUDIT_RETENTION=0)
    def test_deletion_disabled(self, mock_now: Mock) -> None:
        """Verify log files are not deleted when log clearing is disabled."""

        later_time = self.now - timedelta(days=1000)
        self.create_dummy_records(mock_now, later_time)

        mock_now.return_value = self.now
        clear_log_records()

        self.assertEqual(1, AppLog.objects.count())
        self.assertEqual(1, RequestLog.objects.count())
        self.assertEqual(1, AuditLog.objects.count())
