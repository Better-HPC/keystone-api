"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

__all__ = [
    'JobExecutionErrorSerializer',
    'JobResponseSerializer',
    'JobRequestSerializer',
    'JobStepResultSerializer',
    'JobStepSerializer',
    'ReferenceResolutionErrorSerializer',
]


class JobExecutionErrorSerializer(serializers.Serializer):
    """Object serializer for a batch job failure caused by a `JobExecutionError`."""

    detail = serializers.CharField()
    step = serializers.IntegerField()
    status = serializers.IntegerField()
    body = serializers.DictField()


class JobStepResultSerializer(serializers.Serializer):
    """Object serializer for the outcome of a single executed batch step."""

    ref = serializers.CharField(allow_null=True)
    index = serializers.IntegerField()
    method = serializers.CharField()
    path = serializers.CharField()
    status = serializers.IntegerField()
    body = serializers.DictField()


class JobResponseSerializer(serializers.Serializer):
    """Object serializer for a successful batch job."""

    results = JobStepResultSerializer(many=True)


class JobStepSerializer(serializers.Serializer):
    """Object serializer for a single step within a batch job."""

    ref = serializers.CharField(required=False, default='', allow_blank=True)
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


class JobRequestSerializer(serializers.Serializer):
    """Object serializer for a batch job comprising multiple steps."""

    dry_run = serializers.BooleanField(required=False, default=False)
    actions = JobStepSerializer(many=True, allow_empty=False)

    def validate_actions(self, value: list[dict]) -> list[dict]:
        """Ensure all ref aliases within the batch are unique."""

        refs = [a['ref'] for a in value if a.get('ref')]
        if len(refs) != len(set(refs)):
            raise serializers.ValidationError('Reference aliases must be unique within a job.')

        return value


class ReferenceResolutionErrorSerializer(serializers.Serializer):
    """Object serializer for a batch job failure caused by a `ReferenceResolutionError`."""

    detail = serializers.CharField()
    token = serializers.CharField()
