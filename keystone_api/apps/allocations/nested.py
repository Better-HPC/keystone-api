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
    'AllocationSummarySerializer',
    'ClusterSummarySerializer',
    'CommentSummarySerializer',
]


class ClusterSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing cluster names in nested responses."""

    class Meta:
        """Serializer settings."""

        model = Cluster
        fields = ['id', 'name', 'enabled']


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
        fields = ['user', 'content', 'created', 'private', '_user']
