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
    'AllocationRequestSerializer',
    'AllocationRequestReviewSerializer',
    'ClusterSerializer',
]


class AllocationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Allocation` class."""

    class Meta:
        """Serializer settings."""

        model = Allocation
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    """Object serializer for the `Attachment` class."""

    class Meta:
        model = Attachment
        fields = '__all__'


class AllocationRequestSerializer(serializers.ModelSerializer):
    """Object serializer for the `AllocationRequest` class."""

    allocations = AllocationSerializer(source='allocation_set', many=True, required=False)
    attachments = AttachmentSerializer(source='attachment_set', many=True, required=False)

    class Meta:
        """Serializer settings."""

        model = AllocationRequest
        fields = '__all__'

    def create(self, validated_data):
        allocation_request = AllocationRequest.objects.create(**validated_data)

        allocations_data = validated_data.pop('allocations', [])
        for allocation in allocations_data:
            Allocation.objects.create(request=allocation_request, **allocation)

        attachments_data = validated_data.pop('attachments', [])
        for attachment in attachments_data:
            Attachment.objects.create(request=allocation_request, **attachment)

        return allocation_request

    def update(self, instance, validated_data):

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.active = validated_data.get('active', instance.active)
        instance.expire = validated_data.get('expire', instance.expire)
        instance.save()

        # Update allocations
        old_allocations = instance.allocations.all()
        allocations_data = validated_data.pop('allocations', [])
        for allocation_data in allocations_data:
            Allocation.objects.create(request=instance, **allocation_data)

        # Update attachments
        old_attatchments = instance.attachments.all()
        attachments_data = validated_data.pop('attachments', [])
        for attachment in attachments_data:
            Attachment.objects.create(request=instance, **attachment)

        old_allocations.delete()
        old_attatchments.delete()
        return instance


class AllocationRequestReviewSerializer(serializers.ModelSerializer):
    """Object serializer for the `AllocationRequestReview` class."""

    class Meta:
        """Serializer settings."""

        model = AllocationRequestReview
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
