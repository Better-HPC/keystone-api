"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from apps.users.nested import TeamSummarySerializer, UserSummarySerializer
from .models import *

__all__ = ['JobStatsSerializer']


class JobStatsSerializer(serializers.ModelSerializer):
    """Object serializer for the `JobStats` class."""

    _user = UserSummarySerializer(source='user', read_only=True)
    _team = TeamSummarySerializer(source='team', read_only=True)

    class Meta:
        """Serializer settings."""

        model = JobStats
        fields = '__all__'
        read_only = ['team']
