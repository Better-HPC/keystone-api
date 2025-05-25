from rest_framework import serializers

from .models import *

__all__ = [
    'TeamRoleSerializer',
    'TeamSummarySerializer',
    'UserRoleSerializer',
    'UserSummarySerializer',
]


class UserSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing user information in nested responses."""

    class Meta:
        """Serializer settings."""

        model = User
        fields = ["username", "first_name", "last_name", "email"]


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for summarizing team member usernames and roles in nested responses."""

    _user = UserSummarySerializer(source="user", read_only=True)

    class Meta:
        """Serializer settings."""

        model = Membership
        fields = ["id", "user", "role", "_user"]


class TeamSummarySerializer(serializers.ModelSerializer):
    """Serializer for summarizing team information in nested responses."""

    class Meta:
        """Serializer settings."""

        model = Team
        fields = ["name", "is_active"]


class TeamRoleSerializer(serializers.ModelSerializer):
    """Serializer for summarizing team names and roles in nested responses."""

    _team = TeamSummarySerializer(source="team", read_only=True)

    class Meta:
        """Serializer settings."""

        model = Membership
        fields = ["id", "team", "role", "_team"]
