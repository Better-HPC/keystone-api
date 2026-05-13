"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from django.db.models import Avg, Count, DurationField, F, IntegerField, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.allocations.models import AllocationRequest, ResourceAllocation
from apps.notifications.models import Notification
from apps.research_products.models import Grant, Publication
from apps.users.models import Team
from plugins.schemas import FilterGetAutoSchema
from .serializers import *

__all__ = [
    "AllocationRequestStatsView",
    "GrantStatsView",
    "NotificationStatsView",
    "PublicationStatsView",
]


class AbstractTeamStatsView(ABC):
    """Abstract base class for team-based statistics views.

    Filters querysets so non-staff users only see statistics for teams
    they belong to. Staff users see statistics across all teams.

    Subclasses must implement `_summarize()` to compute view-specific
    statistics. This class should be combined with `GenericAPIView` (or a
    subclass) using multiple inheritance. This class must appear before
    `GenericAPIView` in the MRO so that `get_queryset` correctly
    calls through to the DRF base implementation via `super()`.
    """

    @abstractmethod
    def _summarize(self) -> dict:
        """Compute and return summary statistics as a dictionary."""

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by user team membership.

        Non-staff users are only returned records from their own teams.
        Staff users are returned all records.
        """

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            teams = Team.objects.teams_for_user(self.request.user)
            return queryset.filter(team__in=teams)

        return queryset

    def get(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = self.serializer_class(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Statistics"],
        summary="Retrieve aggregated allocation request statistics.",
        description=(
            "Returns cumulative statistics for allocation requests and awards. "
            "Staff users are returned statistics across all teams. "
            "Non-staff users are returned statistics limited to teams where they hold membership."
        ),
    ),
)
class AllocationRequestStatsView(AbstractTeamStatsView, GenericAPIView):
    """View providing aggregated allocation request statistics."""

    queryset = AllocationRequest.objects.all()
    serializer_class = AllocationRequestStatsSerializer
    permission_classes = [IsAuthenticated]
    schema = FilterGetAutoSchema()

    @staticmethod
    def _sum_awarded(filter_q: Q) -> Coalesce:
        """Build a filtered `Sum` over `awarded` with an explicit integer output field.

        Args:
            filter_q: A `Q` expression restricting which rows contribute to the sum.

        Returns:
            A `Coalesce` expression that returns 0 when the filtered set is empty.
        """

        return Coalesce(
            Sum("awarded", filter=filter_q, output_field=IntegerField()),
            0, output_field=IntegerField(),
        )

    def _summarize(self) -> dict:
        """Compute allocation request and award statistics.

        Counts, timing metrics, and award totals are each collapsed into a
        single aggregate query to avoid issuing one query per metric.
        """

        # Cache `now()` so all lifecycle buckets share a single reference point
        now_ts = now()
        qs = self.filter_queryset(self.get_queryset())

        # Query filters for request records by lifecycle stage
        is_pending = Q(status=AllocationRequest.StatusChoices.PENDING)
        is_declined = Q(status=AllocationRequest.StatusChoices.DECLINED)
        is_approved = Q(status=AllocationRequest.StatusChoices.APPROVED)
        is_upcoming = is_approved & Q(active__gt=now_ts)
        is_active = is_approved & Q(active__lte=now_ts, expire__gte=now_ts)
        is_expired = is_approved & Q(expire__lt=now_ts)

        # Single query for request-level counts and timing averages
        request_stats = qs.aggregate(
            request_count=Count("id"),
            request_pending_count=Count("id", filter=is_pending),
            request_declined_count=Count("id", filter=is_declined),
            request_approved_count=Count("id", filter=is_approved),
            request_upcoming_count=Count("id", filter=is_upcoming),
            request_active_count=Count("id", filter=is_active),
            request_expired_count=Count("id", filter=is_expired),
            days_pending_average=Avg(F("active") - F("submitted"), output_field=DurationField()),
            days_active_average=Avg(F("expire") - F("active"), output_field=DurationField()),
        )

        # Reverse-FK lifecycle filters for allocations joined back to requests
        award_pending = Q(request__status=AllocationRequest.StatusChoices.PENDING)
        award_declined = Q(request__status=AllocationRequest.StatusChoices.DECLINED)
        award_approved = Q(request__status=AllocationRequest.StatusChoices.APPROVED)
        award_upcoming = award_approved & Q(request__active__gt=now_ts)
        award_active = award_approved & Q(request__active__lte=now_ts, request__expire__gte=now_ts)
        award_expired = award_approved & Q(request__expire__lt=now_ts)

        # Award totals query the allocations table directly to avoid join
        # row duplication and to collapse nine sums into a single query
        allocations = ResourceAllocation.objects.filter(request__in=qs)
        award_stats = allocations.aggregate(
            su_pending_total=self._sum_awarded(award_pending),
            su_declined_total=self._sum_awarded(award_declined),
            su_approved_total=self._sum_awarded(award_approved),
            su_upcoming_total=self._sum_awarded(award_upcoming),
            su_active_total=self._sum_awarded(award_active),
            su_expired_total=self._sum_awarded(award_expired),
            su_requested_total=Coalesce(Sum("requested"), 0, output_field=IntegerField()),
            su_awarded_total=Coalesce(Sum("awarded"), 0, output_field=IntegerField()),
            su_finalized_total=Coalesce(Sum("final"), 0, output_field=IntegerField()),
        )

        days_pending_average = request_stats["days_pending_average"]
        days_active_average = request_stats["days_active_average"]

        return {
            "request_count": request_stats["request_count"],
            "request_pending_count": request_stats["request_pending_count"],
            "request_approved_count": request_stats["request_approved_count"],
            "request_declined_count": request_stats["request_declined_count"],
            "request_upcoming_count": request_stats["request_upcoming_count"],
            "request_active_count": request_stats["request_active_count"],
            "request_expired_count": request_stats["request_expired_count"],

            "su_pending_total": round(award_stats["su_pending_total"], 2),
            "su_declined_total": round(award_stats["su_declined_total"], 2),
            "su_approved_total": round(award_stats["su_approved_total"], 2),
            "su_upcoming_total": round(award_stats["su_upcoming_total"], 2),
            "su_active_total": round(award_stats["su_active_total"], 2),
            "su_expired_total": round(award_stats["su_expired_total"], 2),
            "su_requested_total": round(award_stats["su_requested_total"], 2),
            "su_awarded_total": round(award_stats["su_awarded_total"], 2),
            "su_finalized_total": round(award_stats["su_finalized_total"], 2),

            "days_pending_average": days_pending_average.days if days_pending_average is not None else None,
            "days_active_average": days_active_average.days if days_active_average is not None else None,
        }


@extend_schema_view(
    get=extend_schema(
        tags=["Statistics"],
        summary="Retrieve aggregated grant statistics.",
        description=(
            "Returns cumulative grant statistics. "
            "Staff users are returned statistics across all teams. "
            "Non-staff users are returned statistics limited to teams where they hold membership."
        ),
    ),
)
class GrantStatsView(AbstractTeamStatsView, GenericAPIView):
    """View providing aggregated grant statistics."""

    queryset = Grant.objects.all()
    serializer_class = GrantStatsSerializer
    permission_classes = [IsAuthenticated]
    schema = FilterGetAutoSchema()

    def _summarize(self) -> dict:
        """Calculate summary statistics for team grants.

        Non-staff users are limited to teams where they are a member. All
        counts and funding aggregates are collapsed into a single query.
        """

        # Cache `now()` so lifecycle buckets share a single reference point
        current = now()
        zero = Decimal("0.00")

        qs = self.filter_queryset(self.get_queryset())

        # Query filters for grant records by lifecycle stage
        is_upcoming = Q(start_date__gt=current)
        is_active = Q(start_date__lte=current, end_date__gt=current)
        is_expired = Q(end_date__lte=current)

        stats = qs.aggregate(
            grant_count=Count("id"),
            upcoming_count=Count("id", filter=is_upcoming),
            active_count=Count("id", filter=is_active),
            expired_count=Count("id", filter=is_expired),
            agency_count=Count("agency", distinct=True),
            funding_total=Coalesce(Sum("amount"), zero),
            funding_upcoming=Coalesce(Sum("amount", filter=is_upcoming), zero),
            funding_active=Coalesce(Sum("amount", filter=is_active), zero),
            funding_expired=Coalesce(Sum("amount", filter=is_expired), zero),
            funding_average=Coalesce(Avg("amount"), zero),
        )

        return {
            "grant_count": stats["grant_count"],
            "upcoming_count": stats["upcoming_count"],
            "active_count": stats["active_count"],
            "expired_count": stats["expired_count"],
            "agency_count": stats["agency_count"],
            "funding_total": round(stats["funding_total"], 2),
            "funding_upcoming": round(stats["funding_upcoming"], 2),
            "funding_active": round(stats["funding_active"], 2),
            "funding_expired": round(stats["funding_expired"], 2),
            "funding_average": round(stats["funding_average"], 2),
        }


@extend_schema_view(
    get=extend_schema(
        tags=["Statistics"],
        summary="Retrieve aggregated user notification statistics.",
        description=(
            "Returns cumulative statistics for user notifications. "
            "Staff users are returned statistics across all users. "
            "Non-staff users are returned statistics limited to their own notifications."
        ),
    ),
)
class NotificationStatsView(GenericAPIView):
    """View providing aggregated notification statistics."""

    queryset = Notification.objects.all()
    serializer_class = NotificationStatsSerializer
    permission_classes = [IsAuthenticated]
    schema = FilterGetAutoSchema()

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by notification owner.

        Non-staff users are only returned their own notifications.
        Staff users are returned all records.
        """

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)

        return queryset

    def get(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        qs = self.filter_queryset(self.get_queryset())
        stats = qs.aggregate(
            total=Count("id"),
            unread=Count("id", filter=Q(read=False)),
        )

        serializer = self.serializer_class(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Statistics"],
        summary="Retrieve aggregated publication statistics.",
        description=(
            "Returns cumulative publication statistics. "
            "Staff users are returned statistics across all teams. "
            "Non-staff users are returned statistics limited to teams where they hold membership."
        ),
    ),
)
class PublicationStatsView(AbstractTeamStatsView, GenericAPIView):
    """View providing aggregated publication statistics."""

    queryset = Publication.objects.all()
    serializer_class = PublicationStatsSerializer
    permission_classes = [IsAuthenticated]
    schema = FilterGetAutoSchema()

    def _summarize(self) -> dict:
        """Calculate summary statistics for team publications.

        Non-staff users are limited to teams where they are a member. All
        counts and the review-time average are collapsed into a single query.
        """

        qs = self.filter_queryset(self.get_queryset())

        # Query filters for publication records by lifecycle stage
        is_draft = Q(submitted__isnull=True, published__isnull=True)
        is_submitted = Q(submitted__isnull=False, published__isnull=True)
        is_accepted = Q(published__isnull=False)
        has_review_window = Q(submitted__isnull=False, published__isnull=False)

        stats = qs.aggregate(
            publications_count=Count("id"),
            draft_count=Count("id", filter=is_draft),
            submitted_count=Count("id", filter=is_submitted),
            accepted_count=Count("id", filter=is_accepted),
            journals_count=Count("journal", distinct=True),
            review_average=Avg(
                F("published") - F("submitted"),
                filter=has_review_window,
                output_field=DurationField(),
            ),
        )

        return {
            "publications_count": stats["publications_count"],
            "draft_count": stats["draft_count"],
            "submitted_count": stats["submitted_count"],
            "accepted_count": stats["accepted_count"],
            "journals_count": stats["journals_count"],
            "review_average": stats["review_average"],
        }
