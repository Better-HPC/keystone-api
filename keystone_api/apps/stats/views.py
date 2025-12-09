"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from decimal import Decimal

from django.db.models import Avg, Case, DurationField, ExpressionWrapper, F, Sum, Value, When
from django.db.models.functions import Coalesce
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
    pagination_class = None

    def _summarize(self) -> dict:
        """Compute allocation request and award statistics."""

        # Base query with useful annotations
        now_ts = now()
        qs = self.filter_queryset(self.get_queryset()).annotate(
            days_pending=ExpressionWrapper(
                F('active') - F('submitted'),
                output_field=DurationField()
            ),
            days_active=ExpressionWrapper(
                F('expire') - F('active'),
                output_field=DurationField()
            )
        )

        # Subqueries based on request lifecycle
        qs_upcoming = qs.filter(status=AllocationRequest.StatusChoices.APPROVED, active__gt=now_ts)
        qs_active = qs.filter(status=AllocationRequest.StatusChoices.APPROVED, active__lte=now_ts, expire__gte=now_ts)
        qs_expired = qs.filter(status=AllocationRequest.StatusChoices.APPROVED, expire__lt=now_ts)

        # Request lifecycle counts
        request_count = qs.count()
        request_pending_count = qs.filter(status=AllocationRequest.StatusChoices.PENDING).count()
        request_declined_count = qs.filter(status=AllocationRequest.StatusChoices.DECLINED).count()
        request_approved_count = qs.filter(status=AllocationRequest.StatusChoices.APPROVED).count()
        request_upcoming_count = qs_upcoming.count()
        request_active_count = qs_active.count()
        request_expired_count = qs_expired.count()

        # Award totals across all related allocations
        su_requested_total = qs.aggregate(total=Sum('allocation__requested'))['total'] or 0
        su_awarded_total = qs.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_finalized_total = qs.aggregate(total=Sum('allocation__final'))['total'] or 0

        su_awarded_upcoming = qs_upcoming.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_awarded_active = qs_active.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_awarded_expired = qs_expired.aggregate(total=Sum('allocation__awarded'))['total'] or 0

        # Award totals per cluster
        clusters = qs.values('allocation__cluster_id').distinct()
        per_cluster_structured = {}
        for cluster in clusters:
            cluster_id = cluster['allocation__cluster_id']
            cluster_qs = qs.filter(allocation__cluster_id=cluster_id)
            cluster_upcoming = cluster_qs.filter(active__gt=now_ts)
            cluster_active = cluster_qs.filter(active__lte=now_ts, expire__gte=now_ts)
            cluster_expired = cluster_qs.filter(expire__lt=now_ts)

            per_cluster_structured[str(cluster_id)] = {
                "su_requested_total": cluster_qs.aggregate(total=Sum('allocation__requested'))['total'] or 0,
                "su_awarded_total": cluster_qs.aggregate(total=Sum('allocation__awarded'))['total'] or 0,
                "su_finalized_total": cluster_qs.aggregate(total=Sum('allocation__final'))['total'] or 0,
                "su_awarded_upcoming": cluster_upcoming.aggregate(total=Sum('allocation__awarded'))['total'] or 0,
                "su_awarded_active": cluster_active.aggregate(total=Sum('allocation__awarded'))['total'] or 0,
                "su_awarded_expired": cluster_expired.aggregate(total=Sum('allocation__awarded'))['total'] or 0,
            }

        # Ratios
        approval_ratio = request_approved_count / request_count if request_count else 0.0
        utilization_ratio = (
            su_finalized_total / su_awarded_total
            if su_awarded_total and su_awarded_total > 0
            else 0.0
        )

        # Timing metrics
        days_pending_average = qs.aggregate(Avg('days_pending'))['days_pending__avg']
        days_active_average = qs.aggregate(Avg('days_active'))['days_active__avg']

        return {
            "request_count": request_count,
            "request_pending_count": request_pending_count,
            "request_approved_count": request_approved_count,
            "request_declined_count": request_declined_count,
            "request_upcoming_count": request_upcoming_count,
            "request_active_count": request_active_count,
            "request_expired_count": request_expired_count,
            "su_requested_total": su_requested_total,
            "su_awarded_total": su_awarded_total,
            "su_awarded_upcoming": su_awarded_upcoming,
            "su_awarded_active": su_awarded_active,
            "su_awarded_expired": su_awarded_expired,
            "su_finalized_total": su_finalized_total,
            "per_cluster": per_cluster_structured,
            "approval_ratio": approval_ratio,
            "utilization_ratio": utilization_ratio,
            "days_pending_average": days_pending_average.days if days_pending_average else None,
            "days_active_average": days_active_average.days if days_active_average else None,
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
    pagination_class = None

    def _summarize(self) -> dict:
        """Calculate summary statistics for team grants.

        Non-staff users are limited to teams where they are a member.
        """

        # Common DB aggregates (wrapped in Coalesce for 0-defaults)
        amount_sum = Coalesce(Sum("amount"), Decimal('0.00'))
        amount_avg = Coalesce(Avg("amount"), Decimal('0.00'))

        # Base querysets for all records and records by lifecycle stage
        qs = self.filter_queryset(self.get_queryset())
        upcoming_qs = qs.filter(start_date__gt=now())
        active_qs = qs.filter(start_date__lte=now(), end_date__gt=now())
        expired_qs = qs.filter(end_date__lte=now())

        # Record counts
        grant_count = qs.count()
        upcoming_count = upcoming_qs.count()
        active_count = active_qs.count()
        expired_count = expired_qs.count()
        agency_count = qs.values("agency").distinct().count()

        # Funding values
        funding_total = qs.aggregate(funding_total=amount_sum)["funding_total"]
        funding_upcoming = upcoming_qs.aggregate(funding_upcoming=amount_sum)["funding_upcoming"]
        funding_active = active_qs.aggregate(funding_active=amount_sum)["funding_active"]
        funding_expired = expired_qs.aggregate(funding_expired=amount_sum)["funding_expired"]
        funding_average = qs.aggregate(funding_average=amount_avg)["funding_average"]

        return {
            "grant_count": grant_count,
            "upcoming_count": upcoming_count,
            "active_count": active_count,
            "expired_count": expired_count,
            "agency_count": agency_count,
            "funding_total": funding_total,
            "funding_upcoming": funding_upcoming,
            "funding_active": funding_active,
            "funding_expired": funding_expired,
            "funding_average": funding_average,
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
    pagination_class = None

    def _summarize(self) -> dict:
        """Calculate summary statistics for team publications.

        Non-staff users are limited to teams where they are a member.
        """

        # Base querys for all records and records by lifecycle stage
        qs = self.filter_queryset(self.get_queryset())
        draft_qs = qs.filter(submitted__isnull=True, published__isnull=True)
        submitted_qs = qs.filter(submitted__isnull=False, published__isnull=True)
        accepted_qs = qs.filter(published__isnull=False)

        # Record counts
        publications_count = qs.count()
        draft_count = draft_qs.count()
        submitted_count = submitted_qs.count()
        accepted_count = accepted_qs.count()
        journals_count = qs.values("journal").distinct().count()

        # Average time spent under review by the journal
        review_avg = qs.annotate(
            review_time=ExpressionWrapper(
                F("published") - F("submitted"),
                output_field=DurationField()
            )
        ).aggregate(
            review_time_avg=Avg(
                Case(
                    When(
                        submitted__isnull=False,
                        published__isnull=False,
                        then=F("review_time")
                    ),
                    default=None
                ))
        )["review_time_avg"]

        return {
            "publications_count": publications_count,
            "draft_count": draft_count,
            "submitted_count": submitted_count,
            "accepted_count": accepted_count,
            "journals_count": journals_count,
            "review_average": review_avg,
        }

    def list(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)
