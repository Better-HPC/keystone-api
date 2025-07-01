"""Serializers for rendering model data in nested representations.

Nested serializers are used to represent related models within parent
objects, enabling nested structures in JSON responses. These serializers
are typically used in read-only operations, where relational context
is important but full model operations are not required.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.logging.models import *
from apps.users.nested import UserSummarySerializer

__all__ = [
    'AuditLogSummarySerializer',
]


class AuditLogSummarySerializer(serializers.ModelSerializer):
    """Object serializer for the `AuditLog` class."""

    _actor = UserSummarySerializer(source='user', read_only=True)
    action = serializers.SerializerMethodField()

    class Meta:
        """Serializer settings."""

        model = AuditLog
        fields = ['id', 'timestamp', 'action', 'actor', '_actor', 'changes']

    @extend_schema_field(str)
    def get_action(self, obj: AuditLog) -> str:
        """Return the action type as a human-readable string."""

        _, as_string = AuditLog.Action.choices[obj.action]
        return as_string
