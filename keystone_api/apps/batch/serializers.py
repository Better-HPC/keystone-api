"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

__all__ = [
    'JobSerializer',
    'JobStepSerializer',
]


class JobStepSerializer(serializers.Serializer):
    """Object serializer for a single step within a batch job."""

    ref = serializers.CharField(required=False, default='')
    method = serializers.ChoiceField(choices={'GET', 'POST', 'PUT', 'PATCH', 'DELETE'})
    path = serializers.CharField(max_length=2048)
    payload = serializers.DictField(required=False, default=dict)
    query_params = serializers.DictField(required=False, default=dict)

    def validate_ref(self, value: str) -> str:
        """Ensure the ref alias contains only alphanumeric characters and underscores.

        The alias is used as the identifier inside `@ref{alias.dotpath}` tokens.
        """

        if value and not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                'Reference aliases may only contain alphanumeric characters and underscores.'
            )

        return value


class JobSerializer(serializers.Serializer):
    """Object serializer for a batch job comprising multiple steps."""

    actions = JobStepSerializer(many=True, allow_empty=False)

    def validate_actions(self, value: list[dict]) -> list[dict]:
        """Ensure all ref aliases within the batch are unique."""

        refs = [a['ref'] for a in value if a.get('ref')]
        if len(refs) != len(set(refs)):
            raise serializers.ValidationError('Reference aliases must be unique within a job.')

        return value
