"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

__all__ = ['ConfigSerializer']


class ConfigSerializer(serializers.Serializer):
    """Serializer for exposing application configuration to the frontend."""

    # Application metadata
    version = serializers.CharField()

    # File upload constraints
    max_upload_size = serializers.IntegerField()
    max_upload_count = serializers.IntegerField()
    allowed_file_types = serializers.ListField(child=serializers.CharField())

    # Feature flags
    ldap_enabled = serializers.BooleanField()

    # Session settings
    session_age = serializers.IntegerField()
