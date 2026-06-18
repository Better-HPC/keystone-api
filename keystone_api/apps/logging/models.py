"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database table and defines low-level defaults
for how the associated table/fields/records are presented by parent interfaces.
"""

import auditlog.models
import django_celery_results.models
from django.db import models

from apps.users.models import User

__all__ = ["AuditLog", "FeedEntry", "RequestLog", "TaskResult"]


class AuditLog(auditlog.models.LogEntry):
    """Proxy model for the auditlog backend."""

    class Meta:
        """Database model settings."""

        proxy = True


class FeedEntry(models.Model):
    """An unmanaged database view containing common fields from all log records.

    This model maps to a database view. Unlike concrete tables, Django's
    migration framework cannot automatically manage schema migrations
    for views. Any schema changes to this model require manual edits
    to the database migration plan.
    """

    class Meta:
        """Database model settings."""

        managed = False
        db_table = 'logging_feedentry'
        ordering = ['-timestamp']
        indexes = []

    class RecordType(models.TextChoices):
        """Define choices for the `record_type` field."""

        REQUEST = 'request', 'Request'
        TASK = 'task', 'Task'
        AUDIT = 'audit', 'Audit'

    id = models.CharField(primary_key=True, max_length=20)
    record_id = models.BigIntegerField()
    record_type = models.CharField(max_length=16, choices=RecordType.choices)
    timestamp = models.DateTimeField()
    summary = models.TextField(null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    cid = models.CharField(max_length=32, null=True, blank=True)
    status = models.CharField(max_length=16, null=True, blank=True)


class RequestLog(models.Model):
    """Log entry for an incoming HTTP request."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["method"]),
            models.Index(fields=["cid", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["endpoint", "timestamp"]),
            models.Index(fields=["remote_address", "timestamp"]),
            models.Index(fields=["response_code", "timestamp"]),
        ]

    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=2048)  # Maximum URL length for most browsers
    response_code = models.PositiveSmallIntegerField()
    remote_address = models.CharField(max_length=40, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    cid = models.CharField(max_length=36, null=True, blank=True)  # Standard UUID length

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class TaskResult(django_celery_results.models.TaskResult):
    """Proxy model for the Celery task result backend."""

    class Meta:
        """Database model settings."""

        proxy = True
