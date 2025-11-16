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
    'PublicationStatsSerializer',
]


class AllocationRequestStatsSerializer(serializers.Serializer):
    """Aggregated statistics for allocation requests and awards."""

    # Request lifecycle metrics
    total_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    declined_count = serializers.IntegerField()
    upcoming_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()

    # Award totals
    su_requested_total = serializers.FloatField()
    su_awarded_total = serializers.FloatField()
    su_awarded_upcoming = serializers.FloatField()
    su_awarded_active = serializers.FloatField()
    su_awarded_expired = serializers.FloatField()
    su_finalized_total = serializers.FloatField()

    # Award totals by cluster
    per_cluster = serializers.DictField(
        child=serializers.DictField(
            child=serializers.FloatField(),
        ),
    )

    # Ratios
    approval_ratio = serializers.FloatField()
    utilization_ratio = serializers.FloatField()

    # Timing metrics
    avg_time_to_activation_days = serializers.FloatField()
    avg_allocation_lifetime_days = serializers.FloatField()


class GrantStatsSerializer(serializers.Serializer):
    """Serializer for aggregated grant statistics."""

    funding_total = serializers.DecimalField(max_digits=17, decimal_places=2, allow_null=True)
    funding_average = serializers.DecimalField(max_digits=17, decimal_places=2, allow_null=True)
    grant_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    agency_count = serializers.IntegerField()


class PublicationStatsSerializer(serializers.Serializer):
    """Serializer for aggregated publication statistics."""

    review_average = serializers.DurationField(allow_null=True)
    publications_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
    journals_count = serializers.IntegerField()
