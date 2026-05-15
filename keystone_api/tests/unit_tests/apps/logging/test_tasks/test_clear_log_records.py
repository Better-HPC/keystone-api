"""Unit tests for the `clear_log_records` task."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings, TestCase

from apps.logging.models import AuditLog, RequestLog, TaskResult
from apps.logging.tasks import clear_log_records


@patch("django.utils.timezone.now")
class ClearLogRecordsMethod(TestCase):
    """Test the deletion of log records."""

    now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    def assert_log_counts(
        self,
        *,
        request: int = None,
        audit: int = None,
        task: int = None,
    ) -> None:
        """Assert the given number of log records exist.

        Args:
            request: The number of expected request logs.
            audit: The number of expected audit logs.
            task: The number of expected task result logs.
        """

        if request is not None:
            self.assertEqual(request, RequestLog.objects.count())

        if audit is not None:
            self.assertEqual(audit, AuditLog.objects.count())

        if task is not None:
            self.assertEqual(task, TaskResult.objects.count())

    def create_dummy_records(self, mock_now: Mock, *timestamps: datetime) -> None:
        """Create a series of log records at the given timestamps.

        Creates a request, audit, and task result log record for each of the given timestamps.

        Args:
            mock_now: Mocked function used to return the current datetime.
            timestamps: The timestamps to create log records for.
        """

        log_count = len(timestamps)
        content_type = ContentType.objects.get_for_model(RequestLog)

        for ts in timestamps:
            mock_now.return_value = ts
            RequestLog.objects.create(
                endpoint="/api",
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

            TaskResult.objects.create(
                task_id=f"task-{ts.timestamp()}",
                status="SUCCESS",
                date_done=ts,
            )

        self.assert_log_counts(request=log_count, audit=log_count, task=log_count)

    @override_settings(LOG_REQ_RETENTION_SEC=4)
    @override_settings(LOG_AUD_RETENTION_SEC=0)
    @override_settings(LOG_TSK_RETENTION_SEC=0)
    def test_request_log_rotation(self, mock_now: Mock) -> None:
        """Verify the `LOG_REQ_RETENTION_SEC` setting enables request log rotation."""

        later_time = self.now + timedelta(seconds=settings.LOG_REQ_RETENTION_SEC)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(request=1, audit=2, task=2)
        self.assertEqual(later_time, RequestLog.objects.first().timestamp)

    @override_settings(LOG_REQ_RETENTION_SEC=0)
    @override_settings(LOG_AUD_RETENTION_SEC=4)
    @override_settings(LOG_TSK_RETENTION_SEC=0)
    def test_audit_log_rotation(self, mock_now: Mock) -> None:
        """Verify the `LOG_AUD_RETENTION_SEC` setting enables audit log rotation."""

        later_time = self.now + timedelta(seconds=settings.LOG_AUD_RETENTION_SEC)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(request=2, audit=1, task=2)
        self.assertEqual(later_time, AuditLog.objects.first().timestamp)

    @override_settings(LOG_REQ_RETENTION_SEC=0)
    @override_settings(LOG_AUD_RETENTION_SEC=0)
    @override_settings(LOG_TSK_RETENTION_SEC=4)
    def test_task_result_rotation(self, mock_now: Mock) -> None:
        """Verify the `LOG_TSK_RETENTION_SEC` setting enables task result log rotation."""

        later_time = self.now + timedelta(seconds=settings.LOG_TSK_RETENTION_SEC)
        self.create_dummy_records(mock_now, self.now, later_time)

        mock_now.return_value = later_time
        clear_log_records()

        self.assert_log_counts(request=2, audit=2, task=1)
        self.assertEqual(later_time, TaskResult.objects.first().date_done)

    @override_settings(LOG_REQ_RETENTION_SEC=0)
    @override_settings(LOG_AUD_RETENTION_SEC=0)
    @override_settings(LOG_TSK_RETENTION_SEC=0)
    def test_deletion_disabled(self, mock_now: Mock) -> None:
        """Verify log files are not deleted when log clearing is disabled."""

        later_time = self.now - timedelta(days=1000)
        self.create_dummy_records(mock_now, later_time)

        mock_now.return_value = self.now
        clear_log_records()

        self.assert_log_counts(request=1, audit=1, task=1)