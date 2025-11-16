"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import Avg, Case, DurationField, ExpressionWrapper, F, Sum, When
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

import plugins.filter
from apps.research_products.models import Grant, Publication
from .serializers import *
from ..allocations.models import AllocationRequest
from ..users.mixins import TeamScopedListMixin

__all__ = ['AllocationRequestStatsViewSet', 'GrantStatsViewSet', 'PublicationStatsViewSet']


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated allocation request statistics.",
        description=(
            "Returns cumulative statistics for allocation requests and awards. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        responses={200: AllocationRequestStatsSerializer},
    ),
)
class AllocationRequestStatsViewSet(TeamScopedListMixin, viewsets.GenericViewSet):
    """ViewSet providing aggregated allocation request statistics globally and per team."""

    queryset = AllocationRequest.objects.all()
    filter_backends = [plugins.filter.AdvancedFilterBackend]
    permission_classes = [IsAuthenticated]

    def _summarize(self) -> dict:
        """Compute allocation request and award statistics."""

        qs = self.filter_queryset(self.get_queryset())

        # Request lifecycle counts
        total_count = qs.count()
        pending_count = qs.filter(status="pending").count()
        approved_count = qs.filter(status="approved").count()
        declined_count = qs.filter(status="declined").count()
        upcoming_count = qs.filter(start_date__gt=now()).count()
        active_count = qs.filter(start_date__lte=now(), end_date__gte=now()).count()
        expired_count = qs.filter(end_date__lt=now()).count()

        # Award totals
        su_requested_total = qs.aggregate(Sum("su_requested"))["su_requested__sum"]
        su_awarded_total = qs.aggregate(Sum("su_awarded"))["su_awarded__sum"]
        su_finalized_total = qs.aggregate(Sum("su_finalized"))["su_finalized__sum"]

        # Award totals per cluster
        per_cluster = (
            qs.values("cluster_id")
            .annotate(
                requested=Sum("su_requested"),
                awarded=Sum("su_awarded"),
                finalized=Sum("su_finalized"),
            )
        )

        per_cluster_structured = {
            str(row["cluster_id"]): {
                "requested": row["requested"],
                "awarded": row["awarded"],
                "finalized": row["finalized"],
            }
            for row in per_cluster
        }

        # Ratios (guard against division by zero)
        approval_ratio = (
            approved_count / total_count if total_count > 0 else 0.0
        )
        utilization_ratio = (
            (su_finalized_total / su_awarded_total)
            if su_awarded_total and su_awarded_total > 0
            else 0.0
        )

        # Timing metrics
        avg_time_to_activation_days = qs.aggregate(
            Avg("time_to_activation_days")
        )["time_to_activation_days__avg"]

        avg_allocation_lifetime_days = qs.aggregate(
            Avg("lifetime_days")
        )["lifetime_days__avg"]

        return {
            "total_count": total_count,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "declined_count": declined_count,
            "upcoming_count": upcoming_count,
            "active_count": active_count,
            "expired_count": expired_count,
            "su_total_requested": su_requested_total,
            "su_total_awarded": su_awarded_total,
            "su_total_finalized": su_finalized_total,
            "per_cluster": per_cluster_structured,
            "approval_ratio": approval_ratio,
            "utilization_ratio": utilization_ratio,
            "avg_time_to_activation_days": avg_time_to_activation_days,
            "avg_allocation_lifetime_days": avg_allocation_lifetime_days,
        }

    def list(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = AllocationRequestStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated grant statistics.",
        description=(
            "Returns cumulative grant statistics. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        responses={200: GrantStatsSerializer},
    ),
)
class GrantStatsViewSet(TeamScopedListMixin, viewsets.GenericViewSet):
    """ViewSet providing aggregated grant statistics globally and per team."""

    queryset = Grant.objects.all()
    filter_backends = [plugins.filter.AdvancedFilterBackend]
    permission_classes = [IsAuthenticated]

    def _summarize(self) -> dict:
        """Calculate summary statistics for team grants.

        Non-staff users are limited to teams where they are a member.
        """

        qs = self.filter_queryset(self.get_queryset())

        grant_count = qs.count()
        active_count = qs.filter(end_date__gte=now()).count()
        expired_count = qs.filter(end_date__lt=now()).count()
        agency_count = qs.values("agency").distinct().count()
        funding_total = qs.aggregate(Sum("amount"))["amount__sum"]
        funding_average = qs.aggregate(Avg("amount"))["amount__avg"]

        return {
            "funding_total": funding_total,
            "funding_average": funding_average,
            "grant_count": grant_count,
            "active_count": active_count,
            "expired_count": expired_count,
            "agency_count": agency_count,
        }

    def list(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = GrantStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated publication statistics.",
        description=(
            "Returns cumulative publication statistics. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        responses={200: PublicationStatsSerializer},
    ),
)
class PublicationStatsViewSet(TeamScopedListMixin, viewsets.GenericViewSet):
    """ViewSet providing aggregated publication statistics globally and per team."""

    queryset = Publication.objects.all()
    filter_backends = [plugins.filter.AdvancedFilterBackend]
    permission_classes = [IsAuthenticated]

    def _summarize(self) -> dict:
        """Calculate summary statistics for team publications.

        Non-staff users are limited to teams where they are a member.
        """

        qs = self.filter_queryset(self.get_queryset())

        publications_count = qs.count()
        submitted_count = qs.filter(submitted__isnull=False).count()
        accepted_count = qs.filter(published__isnull=False).count()
        journals_count = qs.values("journal").distinct().count()

        # Average time spent under review by the journal
        review_avg = qs.annotate(
            review_time=ExpressionWrapper(
                F("published") - F("submitted"),
                output_field=DurationField()
            )
        ).aggregate(
            review_time_avg=Avg(
                Case(When(submitted__isnull=False, published__isnull=False, then=F("review_time")), default=None)
            )
        )["review_time_avg"]

        return {
            "review_average": review_avg,
            "publications_count": publications_count,
            "submitted_count": submitted_count,
            "accepted_count": accepted_count,
            "journals_count": journals_count,
        }

    def list(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)
