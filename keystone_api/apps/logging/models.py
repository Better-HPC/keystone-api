"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

import auditlog.models
import django_celery_results.models
from django.db import models

from apps.users.models import User

__all__ = ['AppLog', 'AuditLog', 'RequestLog', 'TaskResult']


class AppLog(models.Model):
    """An application log entry."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['name', 'level', 'timestamp']),
            models.Index(fields=['pathname', 'lineno']),
        ]

    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10)
    pathname = models.CharField(max_length=260)
    lineno = models.IntegerField()
    message = models.TextField()
    func = models.CharField(max_length=80, blank=True, null=True)
    sinfo = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class RequestLog(models.Model):
    """Log entry for an incoming HTTP request."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['method']),
            models.Index(fields=['endpoint']),

            models.Index(fields=['cid', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['remote_address', 'timestamp']),
            models.Index(fields=['response_code', 'timestamp']),

            models.Index(fields=['cid', 'method', 'timestamp']),
            models.Index(fields=['user', 'method', 'timestamp']),
            models.Index(fields=['endpoint', 'method', 'timestamp']),
            models.Index(fields=['remote_address', 'method', 'timestamp']),
            models.Index(fields=['response_code', 'method', 'timestamp']),
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


class AuditLog(auditlog.models.LogEntry):
    """Proxy model for the auditlog backend."""

    class Meta:
        """Database model settings."""

        proxy = True
