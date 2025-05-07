"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer
from .models import *

__all__ = [
    'AppLogSerializer',
    'AuditLogSerializer',
    'RequestLogSerializer',
    'TaskResultSerializer',
]

User = get_user_model()


class AppLogSerializer(serializers.ModelSerializer):
    """Object serializer for the `AppLog` class."""

    class Meta:
        """Serializer settings."""

        model = AppLog
        fields = '__all__'


class RequestLogSerializer(serializers.ModelSerializer):
    """Object serializer for the `RequestLog` class."""

    _user = UserSummarySerializer(source='user', read_only=True)

    class Meta:
        """Serializer settings."""

        model = RequestLog
        fields = '__all__'


class TaskResultSerializer(serializers.ModelSerializer):
    """Object serializer for the `TaskResult` class."""

    class Meta:
        """Serializer settings."""

        model = TaskResult
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    """Object serializer for the `AuditLog` class."""

    class Meta:
        """Serializer settings."""

        model = AuditLog
        fields = '__all__'
