"""Serializers for rendering model data in nested representations.

Nested serializers are used to represent related models within parent
objects, enabling nested structures in JSON responses. These serializers
are typically used in read-only operations, where relational context
is important but full model operations are not required.
"""

from rest_framework import serializers

from apps.users.models import User
from apps.users.nested import UserSummarySerializer
from .models import *

__all__ = [
    'AllocationRequestSummarySerializer',
    'AllocationInlineSerializer',
    'AllocationSummarySerializer',
    'AttachmentSummarySerializer',
    'ClusterSummarySerializer',
    'CommentSummarySerializer',
]


class ClusterSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing cluster names in nested responses."""

    class Meta:
        """Serializer settings."""

        model = Cluster
        fields = ['id', 'name', 'enabled']


class AllocationInlineSerializer(serializers.Serializer):
    """Accepts cluster and requested service units for inline allocation creation."""

    cluster = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.allocations.models', fromlist=['Cluster']).Cluster.objects.all()
    )
    requested = serializers.IntegerField(min_value=0)


class AllocationRequestSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing allocation requests in nested responses."""

    class Meta:
        """Serializer settings."""

        model = AllocationRequest
        fields = ['id', 'title', 'status', 'active', 'expire']


class AllocationSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing allocated service units in nested responses."""

    _cluster = ClusterSummarySerializer(source='cluster', read_only=True)

    class Meta:
        model = Allocation
        fields = ['id', 'cluster', 'requested', 'awarded', 'final', '_cluster']


class AttachmentSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing file attachments in nested responses."""

    file = serializers.FileField(use_url=False)
    name = serializers.CharField()

    class Meta:
        """Serializer settings."""

        model = Attachment
        fields = ['file', 'name']


class CommentSummarySerializer(serializers.ModelSerializer):
    """Serializer for user comments in nested responses."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    _user = UserSummarySerializer(source='user', read_only=True)

    class Meta:
        """Serializer settings."""

        model = Comment
        fields = ['id', 'user', 'content', 'created', 'private', '_user']
