"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from apps.users.models import User
from apps.users.nested import UserSummarySerializer
from .models import *

__all__ = [
    'NotificationSerializer',
    'PreferenceSerializer',
]


class NotificationSerializer(serializers.ModelSerializer):
    """Object serializer for the `Notification` class."""

    _user = UserSummarySerializer(source='user', read_only=True)

    class Meta:
        """Serializer settings."""

        model = Notification
        fields = ['id', 'time', 'read', 'subject', 'message', 'notification_type', 'user', '_user']
        read_only_fields = [f for f in fields if f != 'read']


class PreferenceSerializer(serializers.ModelSerializer):
    """Object serializer for the `Preference` class."""

    _user = UserSummarySerializer(source='user', read_only=True)

    class Meta:
        """Serializer settings."""

        model = Preference
        fields = '__all__'
        extra_kwargs = {'user': {'required': False}}  # Default value set by the view class

    def validate_user(self, value: User) -> User:
        """Validate the reviewer matches the user submitting the request."""

        request_submitter = self.context['request'].user
        if not (request_submitter.is_staff or value == request_submitter):
            raise serializers.ValidationError("User field cannot be set to a different user than the request submitter.")

        return value
