"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers

from .models import *

__all__ = [
    'PrivilegedUserSerializer',
    'TeamMembershipSerializer',
    'TeamSerializer',
    'RestrictedUserSerializer',
]


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Object serializer for the `TeamMembership` model including all fields."""

    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="username")
    team = serializers.SlugRelatedField(queryset=Team.objects.all(), slug_field="name")

    class Meta:
        """Serializer settings."""

        model = TeamMembership
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    """Object serializer for the `TeamMembership` model including the usernames and roles of each member."""

    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field="username")

    class Meta:
        """Serializer settings."""

        model = TeamMembership
        fields = ["user", "role"]


class TeamRoleSerializer(serializers.ModelSerializer):
    """Object serializer for the `TeamMembership` model including the team names and roles of each member."""

    team = serializers.SlugRelatedField(queryset=Team.objects.all(), slug_field="name")

    class Meta:
        """Serializer settings."""

        model = TeamMembership
        fields = ["team", "role"]
        read_only_fields = ["team", "role"]


class TeamSerializer(serializers.ModelSerializer):
    """Object serializer for the `Team` model."""

    members = UserRoleSerializer(source="teammembership_set", many=True)

    class Meta:
        """Serializer settings."""

        model = Team
        fields = ["name", "members"]

    @transaction.atomic
    def create(self, validated_data: dict) -> Team:
        """Create ad return a new Team from validated data."""

        members_data = validated_data.pop("teammembership_set", [])
        team = Team.objects.create(**validated_data)
        for membership in members_data:
            TeamMembership.objects.create(team=team, user=membership["user"], role=membership["role"])

        return team

    @transaction.atomic
    def update(self, instance: Team, validated_data: dict) -> Team:
        """Update and return an existing Team instance."""

        members_data = validated_data.pop("teammembership_set", [])

        # Update team attributes
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        if self.partial is False:
            instance.teammembership_set.all().delete()

        # Update membership records
        for membership in members_data:
            TeamMembership.objects.update_or_create(
                team=instance, user=membership["user"], role=membership["role"]
            )

        return instance


class PrivilegedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` model including administrative fields."""

    teams = TeamRoleSerializer(source='teammembership_set', many=True)

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
        read_only_fields = ['is_active', 'is_staff', 'is_ldap_user', 'date_joined', 'last_login', 'profile_image', 'teams']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data: dict) -> None:
        """Raises an error when attempting to create a new record.

        Raises:
            RuntimeError: Every time the function is called.
        """

        raise RuntimeError('Attempted to create new user record using a serializer with restricted permissions.')
