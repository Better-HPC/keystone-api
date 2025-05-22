"""Extends the `django-auditlog` package with custom field serialization.

Field serializers convert individual database fields to/from a format suitable
for use in a serialized JSON response. This plugin provides custom serialization
for a records audit history.
"""

from django.db.models import Manager
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field({
    'type': 'object',
    'additionalProperties': {
        'type': 'object',
        'additionalProperties': {
            'type': 'array',
            'items': {'type': 'string'},
            'minItems': 2,
            'maxItems': 2,
        }
    },
    'example': {
        "101": {
            "field1": ["old_value_1", "new_value_1"],
            "field2": ["old_value_2", "new_value_2"]
        },
        "102": {
            "field3": ["old_value_3", "new_value_3"]
        }
    }
})
class AuditlogFieldSerializer(serializers.Field):
    """Read-only serializer field for exposing audit log history.

    Returns a dict of audit entries keyed by ID, with optional support
    for limiting results via the `_history` query parameter.
    """

    def to_representation(self, instance: Manager) -> dict[int, dict]:
        """Serialize a records audit history.

        Args:
            instance: Related audit log manager instance.

        Returns:
            A dictionary mapping record change IDs to the recorded changes.
        """

        request = self.context['request']
        queryset = instance.all().order_by('-id')
        if limit := request.query_params.get('_history'):
            queryset = queryset[:int(limit)]

        return {record.id: record.changes_dict for record in queryset}

    def to_internal_value(self, data: any) -> None:
        """Force read-only behavior by raising an error on deserialization.

        Raises:
            NotImplementedError
        """

        raise NotImplementedError("Audit history is read-only.")
