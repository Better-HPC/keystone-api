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
    'AllocationSerializer',
    'ClusterSerializer',
    'ProposalSerializer',
    'ProposalReviewSerializer',
    'SafeClusterSerializer'
]


class ClusterSerializer(serializers.ModelSerializer):
    """Object serializer for the `Cluster` class"""

    class Meta:
        model = Cluster
        fields = '__all__'


class SafeClusterSerializer(serializers.ModelSerializer):
    """Object serializer for the `Cluster` class that excludes sensitive fields"""

    class Meta:
        model = Cluster
        fields = ('name', 'description', 'enabled')


class AllocationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Allocation` class"""

    class Meta:
        model = Allocation
        fields = '__all__'


class ProposalSerializer(serializers.ModelSerializer):
    """Object serializer for the `AllocationRequest` class"""

    class Meta:
        model = AllocationRequest
        fields = '__all__'


class ProposalReviewSerializer(serializers.ModelSerializer):
    """Object serializer for the `ProposalReview` class"""

    class Meta:
        model = AllocationReview
        fields = '__all__'
        extra_kwargs = {'reviewer': {'required': False}}  # Default reviewer value is set by the endpoint view

    def validate_reviewer(self, value: User) -> User:
        """Validate the reviewer matches the user submitting the request"""

        if value != self.context['request'].user:
            raise serializers.ValidationError("Reviewer cannot be set to a different user than the submitter")

        return value
