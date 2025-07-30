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
        summary="List all research grants",
        description="Retrieve all research grants visible to the current user.",
        tags=["Grants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a research grant",
        description="Retrieve a single research grant by ID.",
        tags=["Grants"],
    ),
    create=extend_schema(
        summary="Create a research grant",
        description="Create a new research grant for review.",
        tags=["Grants"],
    ),
    update=extend_schema(
        summary="Update a research grant",
        description="Replace an existing research grant with new values.",
        tags=["Grants"],
    ),
    partial_update=extend_schema(
        summary="Partially update a research grant",
        description="Apply a partial update to an existing research grant.",
        tags=["Grants"],
    ),
    destroy=extend_schema(
        summary="Delete a research grant",
        description="Delete a research grant by ID.",
        tags=["Grants"],
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
        summary="List all research publications",
        description="Retrieve all research publications visible to the current user.",
        tags=["Publications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a research publication",
        description="Retrieve a single research publication by ID.",
        tags=["Publications"],
    ),
    create=extend_schema(
        summary="Create a research publication",
        description="Create a new research publication for review.",
        tags=["Publications"],
    ),
    update=extend_schema(
        summary="Update a research publication",
        description="Replace an existing research publication with new values.",
        tags=["Publications"],
    ),
    partial_update=extend_schema(
        summary="Partially update a research publication",
        description="Apply a partial update to an existing research publication.",
        tags=["Publications"],
    ),
    destroy=extend_schema(
        summary="Delete a research publication",
        description="Delete a research publication by ID.",
        tags=["Publications"],
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
