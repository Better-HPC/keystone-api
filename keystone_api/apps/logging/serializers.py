"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.serializers import UserSummarySerializer
from .models import *

__all__ = [
    'AppLogSerializer',
    'AuditLogSerializer',
    'RequestLogSerializer',
    'TaskResultSerializer',
]


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

    _actor = UserSummarySerializer(source='user', read_only=True)
    action = serializers.SerializerMethodField()

    class Meta:
        """Serializer settings."""

        model = AuditLog
        fields = ['id', 'object_pk', 'object_id', 'action', 'changes', 'cid', 'remote_addr', 'remote_port', 'timestamp', 'actor', '_actor']

    @extend_schema_field(str)
    def get_action(self, obj: AuditLog) -> str:
        """Return the logged user action as a human-readable string."""

        _, as_string = AuditLog.Action.choices[obj.action]
        return as_string
