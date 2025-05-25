"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers

from apps.logging.nested import AuditLogSummarySerializer
from .models import *
from .nested import *

__all__ = [
    'MembershipSerializer',
    'PrivilegedUserSerializer',
    'RestrictedUserSerializer',
    'TeamSerializer',
]


class MembershipSerializer(serializers.ModelSerializer):
    """Object serializer for the `Membership` model."""

    _user = UserSummarySerializer(source="user", read_only=True)
    _team = TeamSummarySerializer(source="team", read_only=True)
    _history = AuditLogSummarySerializer(source='history', many=True, read_only=True)

    class Meta:
        """Serializer settings."""

        model = Membership
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    """Object serializer for the `Team` model."""

    membership = UserRoleSerializer(many=True, read_only=False, required=False, default=[])
    _history = AuditLogSummarySerializer(source='history', many=True, read_only=True)

    class Meta:
        """Serializer settings."""

        model = Team
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data: dict) -> Team:
        """Create and return a new Team from validated data."""

        members_data = validated_data.pop("membership", [])
        team = Team.objects.create(**validated_data)
        for membership in members_data:
            Membership.objects.create(team=team, user=membership["user"], role=membership["role"])

        return team

    @transaction.atomic
    def update(self, instance: Team, validated_data: dict) -> Team:
        """Update and return an existing Team instance."""

        members_data = validated_data.pop("membership", [])

        # Update team attributes
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        if self.partial is False:
            instance.membership.all().delete()

        # Update membership records
        for membership in members_data:
            Membership.objects.update_or_create(
                team=instance, user=membership["user"], defaults={"role": membership["role"]}
            )

        return instance


class PrivilegedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` model including sensitive fields."""

    membership = TeamRoleSerializer(many=True, read_only=False, required=False, default=[])
    _history = AuditLogSummarySerializer(source='history', read_only=True, many=True)

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

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        """Create and return a new User instance."""

        teams_data = validated_data.pop("membership", [])
        validated_data.pop("groups", None)
        validated_data.pop("user_permissions", None)

        # Passwords are pre-hashed in the validated data dictionary so instances
        # are created directly instead of using the `create_user` factory method.
        user = User.objects.create(**validated_data)

        for team_data in teams_data:
            Membership.objects.create(
                user=user,
                team=team_data["team"],
                role=team_data["role"]
            )

        return user

    @transaction.atomic
    def update(self, instance: User, validated_data: dict) -> User:
        """Update and return an existing User instance."""

        teams_data = validated_data.pop("membership", [])
        validated_data.pop("groups", None)
        validated_data.pop("user_permissions", None)

        # Update user info. Passwords are pre-hashed in the validated data dictionary
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Overwrite existing memberships for `PUT` style operations
        if self.partial is False:
            instance.membership.all().delete()

        # If teams are provided, update memberships
        for team_data in teams_data:
            Membership.objects.update_or_create(
                team=team_data["team"], user=instance, defaults={"role": team_data["role"]}
            )

        instance.save()
        return instance


class RestrictedUserSerializer(PrivilegedUserSerializer):
    """Object serializer for the `User` class with sensitive fields marked as read only."""

    membership = TeamRoleSerializer(many=True, read_only=True)

    class Meta:
        """Serializer settings."""

        model = User
        fields = '__all__'
        read_only_fields = ['is_active', 'is_staff', 'is_ldap_user', 'date_joined', 'last_login', 'profile_image', 'teams']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data: dict) -> None:
        """Prevents creation of new user records by raising an exception.

        Raises:
            RuntimeError: Every time the function is called.
        """

        raise RuntimeError('Attempted to create new user record using a serializer with restricted permissions.')
