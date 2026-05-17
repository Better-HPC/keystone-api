"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from rest_framework import serializers

from apps.logging.nested import AuditLogSummarySerializer
from .models import *
from .nested import *

__all__ = [
    "MembershipSerializer",
    "PrivilegedUserSerializer",
    "RestrictedUserSerializer",
    "TeamSerializer",
]


class MembershipSerializer(serializers.ModelSerializer):
    """Object serializer for the `Membership` model."""

    _user = UserSummarySerializer(source="user", read_only=True)
    _team = TeamSummarySerializer(source="team", read_only=True)
    _history = AuditLogSummarySerializer(source="history", many=True, read_only=True)

    class Meta:
        """Serializer settings."""

        model = Membership
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        """Validate record data.

        Blocks non-staff users from creating memberships for inactive teams.

        Args:
            attrs: The membership attributes to validate.

        Returns:
            A dictionary containing the validated values.
        """

        request = self.context.get("request")
        team = attrs.get("team")

        # Prevent non-staff from creating memberships for inactive teams
        is_non_staff = request and not request.user.is_staff
        is_inactive = team is not None and not team.is_active
        if is_non_staff and is_inactive:
            raise serializers.ValidationError(
                {"team": "Non-staff cannot create a membership for an inactive team."}
            )

        return super().validate(attrs)


class PrivilegedUserSerializer(serializers.ModelSerializer):
    """Object serializer for the `User` model including sensitive fields."""

    display_name = serializers.CharField(read_only=True)
    abbreviation = serializers.CharField(read_only=True)
    _membership = TeamRoleSerializer(source="membership", many=True, read_only=True)
    _history = AuditLogSummarySerializer(source="history", read_only=True, many=True)

    class Meta:
        """Serializer settings."""

        model = User
        fields = "__all__"
        read_only_fields = ["date_joined", "last_login"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs: dict) -> dict:
        """Validate user attributes match the ORM data model.

        Args:
            attrs: The user attributes to validate.

        Returns:
            A dictionary containing the validated values.
        """

        # Hash the password value
        if "password" in attrs:
            password_validation.validate_password(attrs["password"])
            attrs["password"] = make_password(attrs["password"])

        return super().validate(attrs)


class RestrictedUserSerializer(PrivilegedUserSerializer):
    """Object serializer for the `User` class with sensitive fields marked as read only."""

    class Meta:
        """Serializer settings."""

        model = User
        fields = "__all__"
        read_only_fields = ["is_active", "is_staff", "is_ldap_user", "date_joined", "last_login"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data: dict) -> None:
        """Prevent creation of new user records by raising an exception.

        Args:
            validated_data: The data used to create a new user record.

        Raises:
            RuntimeError: Every time the function is called.
        """

        raise RuntimeError("Attempted to create new user record using a serializer with restricted permissions.")


class TeamSerializer(serializers.ModelSerializer):
    """Object serializer for the `Team` model."""

    slug = serializers.SlugField(read_only=True)
    is_active = serializers.BooleanField(default=True)
    _membership = UserRoleSerializer(source="membership", many=True, read_only=True)
    _history = AuditLogSummarySerializer(source="history", many=True, read_only=True)

    class Meta:
        """Serializer settings."""

        model = Team
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        """Validate record data.

        Requires team names to generate unique slug values.
        Blocks non-staff from creating inactive teams.

        Args:
            attrs: The team attributes to validate.

        Returns:
            A dictionary containing the validated values.
        """

        request = self.context.get("request")

        # Prevent non-staff from creating inactive teams
        is_create = self.instance is None
        user_non_staff = request and not request.user.is_staff
        setting_inactive = not attrs.get("is_active", True)
        if is_create and user_non_staff and setting_inactive:
            raise serializers.ValidationError({
                "is_active": "This field cannot be set to False on new records by non-staff users."
            })

        # Ensure team slugs are unique
        if name := attrs.get("name"):
            slug = slugify(name)
            queryset = Team.objects.filter(slug=slug)

            # Exclude the current instance so a patch that leaves the name
            # unchanged does not conflict with its own slug.
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError({"name": "A team with this name already exists."})

            attrs["slug"] = slug

        return super().validate(attrs)
