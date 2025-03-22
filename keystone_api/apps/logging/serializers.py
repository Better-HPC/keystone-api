"""Serializers for casting database models to/from JSON and XML representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

from .models import *

__all__ = ['AppLogSerializer', 'RequestLogSerializer', 'TaskResultSerializer']


class AppLogSerializer(serializers.ModelSerializer):
    """Object serializer for the `AppLog` class."""

    class Meta:
        """Serializer settings."""

        model = AppLog
        fields = '__all__'


class RequestLogSerializer(serializers.ModelSerializer):
    """Object serializer for the `RequestLog` class."""

    class Meta:
        """Serializer settings."""

        model = RequestLog
        fields = '__all__'


class TaskResultSerializer(serializers.ModelSerializer):
    """Object serializer for the `TaskResult` class."""

    class Meta:
        """Serializer settings."""

        model = TaskResult
        fields = '__all__'
