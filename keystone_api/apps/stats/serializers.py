"""Serializers for casting database models to/from JSON representations.

Serializers handle the casting of database models to/from HTTP compatible
representations in a manner that is suitable for use by RESTful endpoints.
They encapsulate object serialization, data validation, and database object
creation.
"""

from rest_framework import serializers

__all__ = ['GrantStatsSerializer', 'PublicationStatsSerializer']


class GrantStatsSerializer(serializers.Serializer):
    """Serializer for aggregated grant statistics."""

    funding_total = serializers.DecimalField(max_digits=17, decimal_places=2, allow_null=True)
    funding_average = serializers.DecimalField(max_digits=17, decimal_places=2, allow_null=True)
    funding_median = serializers.DecimalField(max_digits=17, decimal_places=2, allow_null=True)
    grant_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    agency_count = serializers.IntegerField()
    top_agencies = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )


class PublicationStatsSerializer(serializers.Serializer):
    """Serializer for aggregated publication statistics."""

    review_time_average = serializers.DurationField(allow_null=True)
    review_time_median = serializers.DurationField(allow_null=True)
    publications_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
    journals_count = serializers.IntegerField()
    top_journals = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
