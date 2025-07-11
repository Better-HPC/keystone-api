"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

__all__ = ['LoginSerializer', 'LogoutSerializer']


class LoginSerializer(serializers.Serializer):
    """Data serializer for validating user credentials."""

    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        """Validate the provided user credentials.

        Args:
            attrs: The user credentials to validate.

        Returns:
            A dictionary containing the validated user instance.
        """

        request = self.context.get('request')
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(request=request, username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        return {'user': user}


class LogoutSerializer(serializers.Serializer):
    """Empty serializer provided for compatibility with the `drf_spectacular` documentation tool."""
