"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from .models import *

__all__ = ['GrantSerializer', 'PublicationSerializer']


class PublicationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Publication` class."""

    class Meta:
        """Serializer settings."""

        model = Publication
        fields = '__all__'
        read_only = ['team']


class GrantSerializer(serializers.ModelSerializer):
    """Object serializer for the `Grant` class."""

    class Meta:
        """Serializer settings."""

        model = Grant
        fields = '__all__'
        read_only = ['team']
