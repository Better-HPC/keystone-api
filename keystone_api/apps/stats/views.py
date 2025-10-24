"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from statistics import median

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Sum
from django.db.models.functions import Now
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from apps.research_products.models import Grant, Publication
from apps.users.models import Team
from .serializers import *

__all__ = ['GrantStatsViewSet', 'PublicationStatsViewSet']


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated grant statistics.",
        description=(
            "Returns cumulative grant statistics across all teams visible to the current user. "
            "Staff users receive statistics for all teams; non-staff users are limited to teams "
            "where they hold membership."
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
class GrantStatsViewSet(viewsets.ViewSet):
    """ViewSet providing aggregated grant statistics globally and per team."""

    @staticmethod
    def _summarize(user, team: Team = None) -> dict:
        """Calculate summary statistics for team grants.

        Non-staff users are limited to teams where they are a member.
        """

        qs = Grant.objects.all()

        if not user.is_staff:
            member_teams = Team.objects.filter(memberships__user=user)
            qs = qs.filter(team__in=member_teams)

        if team:
            # Enforce membership restriction
            if not user.is_staff and not team.memberships.filter(user=user).exists():
                raise PermissionDenied("You do not have access to this team’s statistics.")

            qs = qs.filter(team=team)

        total_funding = qs.aggregate(Sum("amount"))["amount__sum"]
        average_funding = qs.aggregate(Avg("amount"))["amount__avg"]

        amounts = list(qs.order_by("amount").values_list("amount", flat=True))
        funding_median = median(amounts) if amounts else None

        active_count = qs.filter(end_date__gte=Now()).count()
        expired_count = qs.filter(end_date__lt=Now()).count()
        agency_count = qs.values("agency").distinct().count()

        top_agencies = (
            qs.values(agency=F("agency"))
            .annotate(
                count=Count("id"),
                total=Sum("amount"),
                average=Avg("amount"),
            )
            .order_by("-count")[:5]
        )

        # Review time calculation
        review_qs = qs.exclude(start_date__isnull=True, end_date__isnull=True).annotate(
            review_time=ExpressionWrapper(
                F("end_date") - F("start_date"), output_field=DurationField()
            )
        )
        review_durations = list(review_qs.values_list("review_time", flat=True))
        review_avg = (
            review_qs.aggregate(Avg("review_time"))["review_time__avg"]
            if review_qs.exists()
            else None
        )
        review_median = median(review_durations) if review_durations else None

        return {
            "funding_total": total_funding,
            "funding_average": average_funding,
            "funding_median": funding_median,
            "grant_count": qs.count(),
            "active_count": active_count,
            "expired_count": expired_count,
            "agency_count": agency_count,
            "top_agencies": list(top_agencies),
            "review_time_average": review_avg,
            "review_time_median": review_median,
        }

    def list(self, request: Request) -> Response:
        """Return global grant statistics across all teams where the user is a member."""

        stats = self._summarize(request.user)
        serializer = GrantStatsSerializer(stats)
        return Response(serializer.data)

    def retrieve(self, request: Request, pk: int) -> Response:
        """Return grant statistics for a specific team."""

        team = Team.objects.get(pk=pk)
        stats = self._summarize(request.user, team)
        serializer = GrantStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List aggregated publication statistics.",
        description=(
            "Returns cumulative publication statistics across all teams visible to the current user. "
            "Staff users receive statistics for all teams; non-staff users are limited to teams "
            "where they hold membership."
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
class PublicationStatsViewSet(viewsets.ViewSet):
    """ViewSet providing aggregated publication statistics globally and per team."""

    @staticmethod
    def _summarize(user, team=None):
        """Calculate summary statistics for team publications.

        Non-staff users are limited to teams where they are a member.
        """

        qs = Publication.objects.all()

        if not user.is_staff:
            member_teams = Team.objects.filter(memberships__user=user)
            qs = qs.filter(team__in=member_teams)

        if team:
            if not user.is_staff and not team.memberships.filter(user=user).exists():
                raise PermissionDenied("You do not have access to this team’s statistics.")
            qs = qs.filter(team=team)

        total_pubs = qs.count()
        submitted_count = qs.filter(submitted__isnull=False).count()
        accepted_count = qs.filter(published__isnull=False).count()
        journals_count = qs.values("journal").distinct().count()

        top_journals = (
            qs.values(journal=F("journal"))
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # Review durations
        review_qs = qs.filter(
            submitted__isnull=False, published__isnull=False
        ).annotate(
            review_time=ExpressionWrapper(
                F("published") - F("submitted"), output_field=DurationField()
            )
        )
        review_durations = list(review_qs.values_list("review_time", flat=True))
        review_avg = (
            review_qs.aggregate(Avg("review_time"))["review_time__avg"]
            if review_qs.exists()
            else None
        )
        review_median = median(review_durations) if review_durations else None

        return {
            "publications_count": total_pubs,
            "submitted_count": submitted_count,
            "accepted_count": accepted_count,
            "journals_count": journals_count,
            "top_journals": list(top_journals),
            "review_time_average": review_avg,
            "review_time_median": review_median,
        }

    def list(self, request: Request) -> Response:
        """Return global publication statistics across all teams where the user is a member."""

        stats = self._summarize(request.user)
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)

    def retrieve(self, request: Request, pk: int) -> Response:
        """Return grant statistics for a specific team."""

        team = Team.objects.get(pk=pk)
        stats = self._summarize(request.user, team)
        serializer = PublicationStatsSerializer(stats)
        return Response(serializer.data)
