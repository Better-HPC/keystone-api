"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

import django_celery_results.models
from django.db import models

from apps.users.models import User

__all__ = ['AppLog', 'RequestLog', 'TaskResult']


class AppLog(models.Model):
    """An application log entry."""

    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10)
    pathname = models.CharField(max_length=260)
    lineno = models.IntegerField()
    message = models.TextField()
    func = models.CharField(max_length=80, blank=True, null=True)
    sinfo = models.TextField(blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True)


class RequestLog(models.Model):
    """Log entry for an incoming HTTP request."""

    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=2048)  # Maximum URL length for most browsers
    response_code = models.PositiveSmallIntegerField()
    remote_address = models.CharField(max_length=40, null=True)
    time = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class TaskResult(django_celery_results.models.TaskResult):
    """Proxy model for the Celery task result backend."""

    class Meta:
        """Database model settings."""

        proxy = True
