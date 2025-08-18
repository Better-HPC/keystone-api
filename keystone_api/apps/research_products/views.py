"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.users.mixins import TeamScopedListMixin
from .models import *
from .permissions import *
from .serializers import *

__all__ = ['GrantViewSet', 'PublicationViewSet']


@extend_schema_view(
    list=extend_schema(
        summary="List all research grants.",
        description=(
            "Returns a list of all research grants belonging to teams where the user is a member. "
            "Administrators are returned all records regardless of the parent team"
        ),
        tags=["Research - Grants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a research grant.",
        description=(
            "Returns a single research grant by its ID. "
            "Users may only access records for teams they belong to."
        ),
        tags=["Research - Grants"],
    ),
    create=extend_schema(
        summary="Create a research grant.",
        description=(
            "Create a new research grant. "
            "Users may only create records for teams they belong to."
        ),
        tags=["Research - Grants"],
    ),
    update=extend_schema(
        summary="Update a research grant.",
        description=(
            "Replaces an existing research grant with new values. "
            "Users may only modify records for teams they belong to."
        ),
        tags=["Research - Grants"],
    ),
    partial_update=extend_schema(
        summary="Partially update a research grant.",
        description=(
            "Partially update an existing research grant with new values. "
            "Users may only modify records for teams they belong to."
        ),
        tags=["Research - Grants"],
    ),
    destroy=extend_schema(
        summary="Delete a research grant.",
        description=(
            "Deletes a single research grant by its ID. "
            "Users may only delete records for teams they belong to."
        ),
        tags=["Research - Grants"],
    ),
)
class GrantViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing funding awards and grant information."""

    model = Grant
    team_field = 'team'

    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]
    search_fields = ['title', 'agency', 'team__name']
    serializer_class = GrantSerializer
    queryset = Grant.objects.prefetch_related(
        'history'
    ).select_related(
        'team'
    )


@extend_schema_view(
    list=extend_schema(
        summary="List all publications.",
        description=(
            "Returns a list of all publications belonging to teams where the user is a member. "
            "Administrators are returned all records regardless of the parent team"
        ),
        tags=["Research - Publications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a publications.",
        description=(
            "Returns a single publications by its ID. "
            "Users may only access records for teams they belong to."
        ),
        tags=["Research - Publications"],
    ),
    create=extend_schema(
        summary="Create a publications.",
        description=(
            "Create a new publications. "
            "Users may only create records for teams they belong to."
        ),
        tags=["Research - Publications"],
    ),
    update=extend_schema(
        summary="Update a publications.",
        description=(
            "Replaces an existing publications with new values. "
            "Users may only modify records for teams they belong to."
        ),
        tags=["Research - Publications"],
    ),
    partial_update=extend_schema(
        summary="Partially update a publications.",
        description=(
            "Partially update an existing publications with new values. "
            "Users may only modify records for teams they belong to."
        ),
        tags=["Research - Publications"],
    ),
    destroy=extend_schema(
        summary="Delete a publications.",
        description=(
            "Deletes a single publications by its ID. "
            "Users may only delete records for teams they belong to."
        ),
        tags=["Research - Publications"],
    ),
)
class PublicationViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing research publications."""

    model = Publication
    team_field = 'team'

    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]
    search_fields = ['title', 'abstract', 'journal', 'doi', 'team__name']
    serializer_class = PublicationSerializer
    queryset = Publication.objects.prefetch_related(
        'history'
    ).select_related(
        'team'
    )
