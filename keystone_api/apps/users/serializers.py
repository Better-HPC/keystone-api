"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import *

__all__ = [
    'PrivilegeUserSerializer',
    'ResearchGroupSerializer',
    'RestrictedUserSerializer'
]


class ResearchGroupSerializer(serializers.ModelSerializer):
    """Object serializer for the `ResearchGroup` class"""

    class Meta:
        """Serializer settings"""

        model = ResearchGroup
        fields = '__all__'


class RestrictedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` class with administrative fields marked as read only"""

    password = serializers.CharField(write_only=True)

    class Meta:
        """Serializer settings"""

        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_ldap_user', 'password']
        read_only_fields = ['is_staff', 'is_active', 'is_ldap_user']

    def create(self, validated_data: dict) -> None:
        """Raises an error when attempting to create a new record

        Raises:
            RuntimeError: Every time the function is called
        """

        raise RuntimeError('Attempted to create new user record using a serializer with restricted permissions.')

    def update(self, instance: User, validated_data: dict) -> User:
        """Update a given database record with the given data

        Args:
            instance: A `User` record reflecting current database values
            validated_data: The new values to set on the instance

        Returns:
            An instance reflecting the new database state
        """

        if 'password' in validated_data:
            password = validated_data.pop('password')
            password_validation.validate_password(password)
            instance.set_password(password)

        return super().update(instance, validated_data)


class PrivilegeUserSerializer(RestrictedUserSerializer):
    """Object serializer for the `User` class"""

    password = serializers.CharField(write_only=True)

    class Meta:
        """Serializer settings"""

        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_ldap_user', 'password']

    def create(self, validated_data: dict) -> User:
        """Create a new user

        Args:
            validated_data: Validated user data

        Returns:
            A new user instance
        """

        # Use `create_user` instead of `create` to ensure passwords are salted/hashed properly
        return User.objects.create_user(**validated_data)
