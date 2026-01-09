"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

__all__ = [
    'AllocationRequestStatsSerializer',
    'GrantStatsSerializer',
    'NotificationStatsSerializer',
    'PublicationStatsSerializer',
]


class AllocationRequestStatsSerializer(serializers.Serializer):
    """Aggregated statistics for allocation requests and awards."""

    # Request lifecycle metrics
    request_count = serializers.IntegerField()
    request_pending_count = serializers.IntegerField()
    request_approved_count = serializers.IntegerField()
    request_declined_count = serializers.IntegerField()
    request_upcoming_count = serializers.IntegerField()
    request_active_count = serializers.IntegerField()
    request_expired_count = serializers.IntegerField()

    # Award totals
    su_pending_total = serializers.FloatField()
    su_declined_total = serializers.FloatField()
    su_approved_total = serializers.FloatField()
    su_upcoming_total = serializers.FloatField()
    su_active_total = serializers.FloatField()
    su_expired_total = serializers.FloatField()
    su_requested_total = serializers.FloatField()
    su_awarded_total = serializers.FloatField()
    su_finalized_total = serializers.FloatField()

    # Timing metrics
    days_pending_average = serializers.FloatField()
    days_active_average = serializers.FloatField()


class GrantStatsSerializer(serializers.Serializer):
    """Serializer for aggregated grant statistics."""

    grant_count = serializers.IntegerField()
    upcoming_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    agency_count = serializers.IntegerField()

    funding_total = serializers.DecimalField(max_digits=17, decimal_places=2)
    funding_upcoming = serializers.DecimalField(max_digits=17, decimal_places=2)
    funding_active = serializers.DecimalField(max_digits=17, decimal_places=2)
    funding_expired = serializers.DecimalField(max_digits=17, decimal_places=2)
    funding_average = serializers.DecimalField(max_digits=17, decimal_places=2)


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for aggregated notification statistics."""

    total = serializers.IntegerField()
    unread = serializers.IntegerField()


class PublicationStatsSerializer(serializers.Serializer):
    """Serializer for aggregated publication statistics."""

    publications_count = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
    journals_count = serializers.IntegerField()

    review_average = serializers.DurationField(allow_null=True)
