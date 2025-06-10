"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from apps.users.nested import UserSummarySerializer
from .models import *

__all__ = [
    'NotificationSerializer',
    'PreferenceSerializer',
]


class NotificationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Notification` class."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    _user = UserSummarySerializer(read_only=True)

    class Meta:
        """Serializer settings."""

        model = Notification
        fields = '__all__'


class PreferenceSerializer(serializers.ModelSerializer):
    """Object serializer for the `Preference` class."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    _user = UserSummarySerializer(read_only=True)

    class Meta:
        """Serializer settings."""

        model = Preference
        fields = '__all__'
