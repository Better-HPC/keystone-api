"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from django.db.models import Avg, Case, DurationField, ExpressionWrapper, F, QuerySet, Sum, When
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from sympy import false

from apps.allocations.models import AllocationRequest
from apps.notifications.models import Notification
from apps.research_products.models import Grant, Publication
from apps.users.models import Team
from .serializers import *

__all__ = [
    'AllocationRequestStatsView',
    'GrantStatsView',
    'NotificationStatsView',
    'PublicationStatsView'
]

TEAM_QUERY_PARAM = OpenApiParameter(
    name='team',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
)


class AbstractTeamStatsView(ABC):
    """Abstract base class for team-based statistics views."""

    @abstractmethod
    def _summarize(self) -> dict:
        """Compute and return summary statistics as a dictionary."""

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by user team membership for list actions."""

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            teams = Team.objects.teams_for_user(self.request.user)
            return queryset.filter(team__in=teams)

        return queryset

    def get(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        stats = self._summarize()
        serializer = self.serializer_class(stats)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve aggregated allocation request statistics.",
        description=(
            "Returns cumulative statistics for allocation requests and awards. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        parameters=[TEAM_QUERY_PARAM]
    ),
)
class AllocationRequestStatsView(AbstractTeamStatsView, GenericAPIView):
    """ViewSet providing aggregated allocation request statistics."""

    queryset = AllocationRequest.objects.all()
    serializer_class = AllocationRequestStatsSerializer
    permission_classes = [IsAuthenticated]

    def _summarize(self) -> dict:
        """Compute allocation request and award statistics."""

        # Base query with useful annotations
        now_ts = now()
        qs = self.filter_queryset(self.get_queryset())

        # Subqueries based on request lifecycle
        qs_pending = qs.filter(status=AllocationRequest.StatusChoices.PENDING)
        qs_declined = qs.filter(status=AllocationRequest.StatusChoices.DECLINED)
        qs_approved = qs.filter(status=AllocationRequest.StatusChoices.APPROVED)

        qs_upcoming = qs_approved.filter(active__gt=now_ts)
        qs_active = qs_approved.filter(active__lte=now_ts, expire__gte=now_ts)
        qs_expired = qs_approved.filter(expire__lt=now_ts)

        # Request lifecycle counts
        request_count = qs.count()
        request_pending_count = qs_pending.count()
        request_declined_count = qs_declined.count()
        request_approved_count = qs_approved.count()
        request_upcoming_count = qs_upcoming.count()
        request_active_count = qs_active.count()
        request_expired_count = qs_expired.count()

        # Award totals across all related allocations
        su_pending_total = qs_pending.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_declined_total = qs_declined.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_approved_total = qs_approved.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_upcoming_total = qs_upcoming.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_active_total = qs_active.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_expired_total = qs_expired.aggregate(total=Sum('allocation__awarded'))['total'] or 0

        su_requested_total = qs.aggregate(total=Sum('allocation__requested'))['total'] or 0
        su_awarded_total = qs.aggregate(total=Sum('allocation__awarded'))['total'] or 0
        su_finalized_total = qs.aggregate(total=Sum('allocation__final'))['total'] or 0

        # Timing metrics
        qs_annotated = qs.annotate(
            days_pending=ExpressionWrapper(
                F('active') - F('submitted'), output_field=DurationField()
            ),
            days_active=ExpressionWrapper(
                F('expire') - F('active'), output_field=DurationField()
            )
        )

        days_pending_average = qs_annotated.aggregate(Avg('days_pending'))['days_pending__avg']
        days_active_average = qs_annotated.aggregate(Avg('days_active'))['days_active__avg']

        return {
            "request_count": request_count,
            "request_pending_count": request_pending_count,
            "request_approved_count": request_approved_count,
            "request_declined_count": request_declined_count,
            "request_upcoming_count": request_upcoming_count,
            "request_active_count": request_active_count,
            "request_expired_count": request_expired_count,

            "su_pending_total": su_pending_total,
            "su_declined_total": su_declined_total,
            "su_approved_total": su_approved_total,
            "su_upcoming_total": su_upcoming_total,
            "su_active_total": su_active_total,
            "su_expired_total": su_expired_total,
            "su_requested_total": su_requested_total,
            "su_awarded_total": su_awarded_total,
            "su_finalized_total": su_finalized_total,

            "days_pending_average": days_pending_average.days if days_pending_average else None,
            "days_active_average": days_active_average.days if days_active_average else None,
        }


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve aggregated grant statistics.",
        description=(
            "Returns cumulative grant statistics. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        parameters=[TEAM_QUERY_PARAM]
    ),
)
class GrantStatsView(AbstractTeamStatsView, GenericAPIView):
    """ViewSet providing aggregated grant statistics."""

    queryset = Grant.objects.all()
    serializer_class = GrantStatsSerializer
    permission_classes = [IsAuthenticated]

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


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve aggregated user notification statistics.",
        description=(
            "Returns cumulative statistics for user notifications. "
            "Staff users receive statistics for all users. "
            "Non-staff users are limited to their own notifications."
        ),
        tags=["Statistics"],
    ),
)
class NotificationStatsView(GenericAPIView):
    """ViewSet providing aggregated notification statistics."""

    queryset = Notification.objects.all()
    serializer_class = NotificationStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by user team membership for list actions."""

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)

        return queryset

    def get(self, request: Request) -> Response:
        """Return statistics calculated from records matching user permissions and query params."""

        qs = self.get_queryset()
        serializer = self.serializer_class({
            "total": qs.count(),
            "unread": qs.filter(read=false).count(),
        })

        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve aggregated publication statistics.",
        description=(
            "Returns cumulative publication statistics. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        parameters=[TEAM_QUERY_PARAM]
    ),
)
class PublicationStatsView(AbstractTeamStatsView, GenericAPIView):
    """ViewSet providing aggregated publication statistics."""

    queryset = Publication.objects.all()
    serializer_class = PublicationStatsSerializer
    permission_classes = [IsAuthenticated]

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
