"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import *

__all__ = [
    'PrivilegedUserSerializer',
    'TeamMembershipSerializer',
    'TeamSerializer',
    'RestrictedUserSerializer',
]


class TeamSerializer(serializers.ModelSerializer):
    """Object serializer for the `Team` model."""

    class Meta:
        """Serializer settings."""

        model = Team
        fields = '__all__'


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Object serializer for the `TeamMembership` model."""

    class Meta:
        """Serializer settings."""

        model = TeamMembership
        fields = '__all__'


class PrivilegedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` model including administrative fields."""

    class Meta:
        """Serializer settings."""

        model = User
        fields = '__all__'
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs: dict) -> None:
        """Validate user attributes match the ORM data model.

        Args:
            attrs: Dictionary of user attributes.
        """

        # Hash the password value
        if 'password' in attrs:  # pragma: no branch
            password_validation.validate_password(attrs['password'])
            attrs['password'] = make_password(attrs['password'])

        return super().validate(attrs)


class RestrictedUserSerializer(PrivilegedUserSerializer):
    """Object serializer for the `User` class with administrative fields marked as read only."""

    class Meta:
        """Serializer settings."""

        model = User
        fields = '__all__'
        read_only_fields = ['is_active', 'is_staff', 'is_ldap_user', 'date_joined', 'last_login', 'profile_image']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data: dict) -> None:
        """Raises an error when attempting to create a new record.

        Raises:
            RuntimeError: Every time the function is called.
        """

        raise RuntimeError('Attempted to create new user record using a serializer with restricted permissions.')
