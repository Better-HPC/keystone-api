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

    membership = serializers.SerializerMethodField()

    class Meta:
        """Serializer settings."""

        model = Team
        fields = ['id', 'name', 'is_active', 'membership']

    def get_membership(self, obj: Team) -> dict:
        """Return a mapping of usernames to user roles."""

        return {mem.user.username: mem.role for mem in obj.teammembership_set.all()}


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Object serializer for the `TeamMembership` model."""

    user = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    class Meta:
        """Serializer settings."""

        model = TeamMembership
        fields = '__all__'

    def get_user(self, obj: TeamMembership) -> str:
        """Return the user's username."""

        return obj.user.username

    def get_team(self, obj: TeamMembership) -> str:
        """Return the team's name."""

        return obj.team.name


class PrivilegedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` model including administrative fields."""

    membership = serializers.SerializerMethodField()

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

    def get_membership(self, obj: User) -> dict:
        """Return a mapping of team names to membership roles."""

        return {mem.team.name: mem.role for mem in obj.teammembership_set.all()}


class RestrictedUserSerializer(PrivilegedUserSerializer):
    """Object serializer for the `User` class with administrative fields marked as read only."""

    class Meta:
        """Serializer settings."""

        model = User
        fields = '__all__'
        read_only_fields = ['is_active', 'is_staff', 'is_ldap_user', 'date_joined', 'last_login', 'profile_image', 'membership']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data: dict) -> None:
        """Raises an error when attempting to create a new record.

        Raises:
            RuntimeError: Every time the function is called.
        """

        raise RuntimeError('Attempted to create new user record using a serializer with restricted permissions.')
