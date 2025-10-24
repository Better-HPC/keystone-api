"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import Avg, Case, DurationField, ExpressionWrapper, F, QuerySet, Sum, When
from django.db.models.functions import Now
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.research_products.models import Grant, Publication
from apps.users.models import Team
from .serializers import *
from ..research_products.permissions import IsTeamMember
from ..users.mixins import TeamScopedListMixin

__all__ = ['GrantStatsViewSet', 'PublicationStatsViewSet']


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated grant statistics.",
        description=(
            "Returns cumulative grant statistics across all teams. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        responses={200: GrantStatsSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve aggregated grant statistics for a specific team.",
        description=(
            "Returns grant statistics scoped to a specific team. "
            "Access is restricted to staff users or team members."
        ),
        tags=["Statistics"],
        responses={200: GrantStatsSerializer},
    ),
)
class GrantStatsViewSet(TeamScopedListMixin, viewsets.ViewSet):
    """ViewSet providing aggregated grant statistics globally and per team."""

    permission_classes = [IsAuthenticated, IsTeamMember]

    def get_queryset(self) -> QuerySet:
        """Returns the base queryset.

        Required by the `TeamScopedListMixin` mixin.
        """

        return Grant.objects.all()

    def _summarize(self, team: Team = None) -> dict:
        """Calculate summary statistics for team grants.

        Non-staff users are limited to teams where they are a member.
        """

        qs = self.get_queryset()
        if team:
            qs = qs.filter(team=team)

        funding_total = qs.aggregate(Sum("amount"))["amount__sum"]
        funding_average = qs.aggregate(Avg("amount"))["amount__avg"]
        grant_count = qs.count()
        active_count = qs.filter(end_date__gte=Now()).count()
        expired_count = qs.filter(end_date__lt=Now()).count()
        agency_count = qs.values("agency").distinct().count()

        return {
            "funding_total": funding_total,
            "funding_average": funding_average,
            "grant_count": grant_count,
            "active_count": active_count,
            "expired_count": expired_count,
            "agency_count": agency_count,
        }

    def list(self, request: Request) -> Response:
        """Return global grant statistics across all teams where the user is a member."""

        stats = self._summarize(request.user)
        serializer = GrantStatsSerializer(stats)
        return Response(serializer.data)

    def retrieve(self, request: Request, pk: int) -> Response:
        """Return grant statistics for a specific team."""

        team = Team.objects.get(pk=pk)
        stats = self._summarize(team)
        serializer = GrantStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated publication statistics.",
        description=(
            "Returns cumulative publication statistics across all teams. "
            "Staff users receive statistics for all teams. "
            "Non-staff users are limited to teams where they hold membership."
        ),
        tags=["Statistics"],
        responses={200: PublicationStatsSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve aggregated publication statistics for a specific team.",
        description=(
            "Returns publication statistics scoped to a specific team. "
            "Access is restricted to staff users or team members."
        ),
        tags=["Statistics"],
        responses={200: PublicationStatsSerializer},
    ),
)
class PublicationStatsViewSet(TeamScopedListMixin, viewsets.ViewSet):
    """ViewSet providing aggregated publication statistics globally and per team."""

    permission_classes = [IsAuthenticated, IsTeamMember]

    def get_queryset(self) -> QuerySet:
        """Returns the base queryset.

        Required by the `TeamScopedListMixin` mixin.
        """

        return Publication.objects.all()

    def _summarize(self, team: Team = None) -> dict:
        """Calculate summary statistics for team publications.

        Non-staff users are limited to teams where they are a member.
        """

        qs = self.get_queryset()
        if team:
            qs = qs.filter(team=team)

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
        """Return global publication statistics across all teams where the user is a member."""

        stats = self._summarize(request.user)
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)

    def retrieve(self, request: Request, pk: int) -> Response:
        """Return grant statistics for a specific team."""

        team = Team.objects.get(pk=pk)
        stats = self._summarize(team)
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)
