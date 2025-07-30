"""Serializers for rendering model data in nested representations.

Nested serializers are used to represent related models within parent
objects, enabling nested structures in JSON responses. These serializers
are typically used in read-only operations, where relational context
is important but full model operations are not required.
"""

from rest_framework import serializers

from .models import *

__all__ = ['GrantSummarySerializer', 'PublicationSummarySerializer']


class GrantSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing grant information in nested representations."""

    class Meta:
        """Serializer settings."""

        model = Grant
        fields = '__all__'
        read_only = ['team']


class PublicationSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing publication information in nested representations."""

    class Meta:
        """Serializer settings."""

        model = Publication
        fields = '__all__'
        read_only = ['team']
