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

        # Lifecycle subsets
        qs_upcoming = qs.filter(active__gt=now_ts)
        qs_active = qs.filter(active__lte=now_ts, expire__gte=now_ts)
        qs_expired = qs.filter(expire__lt=now_ts)

        # Request lifecycle counts
        request_count = qs.count()
        request_pending_count = qs.filter(status=AllocationRequest.StatusChoices.PENDING).count()
        request_approved_count = qs.filter(status=AllocationRequest.StatusChoices.APPROVED).count()
        request_declined_count = qs.filter(status=AllocationRequest.StatusChoices.DECLINED).count()
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
