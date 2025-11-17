"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

__all__ = ['clear_log_records']


@shared_task()
def clear_log_records() -> None:
    """Delete request and application logs according to retention policies set in application settings."""

    from .models import RequestLog, AuditLog, TaskResult

    # (model, retention interval, datetime field used for pruning)
    log_configs = [
        (RequestLog, settings.LOG_REQ_RETENTION_SEC, "timestamp"),
        (AuditLog, settings.LOG_AUD_RETENTION_SEC, "timestamp"),
        (TaskResult, settings.LOG_TSK_RETENTION_SEC, "date_done"),
    ]

    now = timezone.now()
    for model, retention, field in log_configs:
        if retention > 0:
            cutoff = now - timedelta(seconds=retention)
            model.objects.filter(**{f"{field}__lte": cutoff}).delete()
