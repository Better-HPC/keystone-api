"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone


@shared_task()
def clear_log_files() -> None:
    """Delete request and application logs according to retention policies set in application settings."""

    from .models import AppLog, RequestLog

    if settings.CONFIG_LOG_RETENTION > 0:
        max_app_log_age = timezone.now() - timedelta(seconds=settings.CONFIG_LOG_RETENTION)
        AppLog.objects.filter(time__lt=max_app_log_age).delete()

    if settings.CONFIG_REQUEST_RETENTION > 0:
        max_request_log_age = timezone.now() - timedelta(seconds=settings.CONFIG_REQUEST_RETENTION)
        RequestLog.objects.filter(time__lt=max_request_log_age).delete()
