"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from apps.users.models import User
from .models import *

__all__ = [
    'AttachmentSerializer',
    'AllocationSerializer',
    'AllocationRequestSerializer',
    'AllocationReviewSerializer',
    'ClusterSerializer',
]


class AttachmentSerializer(serializers.ModelSerializer):
    """Object serializer for the `Attachment` class."""

    path = serializers.FileField(use_url=False, read_only=True)

    class Meta:
        """Serializer settings."""

        model = Attachment
        fields = '__all__'


class AllocationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Allocation` class."""

    class Meta:
        """Serializer settings."""

        model = Allocation
        fields = '__all__'


class AllocationRequestSerializer(serializers.ModelSerializer):
    """Object serializer for the `AllocationRequest` class."""

    class Meta:
        """Serializer settings."""

        model = AllocationRequest
        fields = '__all__'


class AllocationReviewSerializer(serializers.ModelSerializer):
    """Object serializer for the `AllocationReview` class."""

    class Meta:
        """Serializer settings."""

        model = AllocationReview
        fields = '__all__'
        extra_kwargs = {'reviewer': {'required': False}}  # Default reviewer value is set by the view class

    def validate_reviewer(self, value: User) -> User:
        """Validate the reviewer matches the user submitting the request."""

        if value != self.context['request'].user:
            raise serializers.ValidationError("Reviewer cannot be set to a different user than the submitter")

        return value


class ClusterSerializer(serializers.ModelSerializer):
    """Object serializer for the `Cluster` class."""

    class Meta:
        """Serializer settings."""

        model = Cluster
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    """Object serializer for the `Comment` class."""

    class Meta:
        """Serializer settings."""

        model = Comment
        fields = '__all__'
