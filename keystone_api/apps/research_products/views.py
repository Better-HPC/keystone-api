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
        summary="List funding grants.",
        description="Returns a filtered list of funding grants.",
        tags=["Research - Grants"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a funding grant.",
        description="Returns a single funding grant by its ID.",
        tags=["Research - Grants"],
    ),
    create=extend_schema(
        summary="Create a funding grant.",
        description="Create a new funding grant.",
        tags=["Research - Grants"],
    ),
    update=extend_schema(
        summary="Update a funding grant.",
        description="Replaces an existing funding grant with new values.",
        tags=["Research - Grants"],
    ),
    partial_update=extend_schema(
        summary="Partially update a funding grant.",
        description="Partially updates an existing funding grant with new values.",
        tags=["Research - Grants"],
    ),
    destroy=extend_schema(
        summary="Delete a funding grant.",
        description="Deletes a single funding grant by its ID.",
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
        summary="List publications.",
        description="Returns a filtered list of publications.",
        tags=["Research - Publications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a publication.",
        description="Returns a single publication by its ID.",
        tags=["Research - Publications"],
    ),
    create=extend_schema(
        summary="Create a publication.",
        description="Create a new publication.",
        tags=["Research - Publications"],
    ),
    update=extend_schema(
        summary="Update a publication.",
        description="Replaces an existing publication with new values.",
        tags=["Research - Publications"],
    ),
    partial_update=extend_schema(
        summary="Partially update a publication.",
        description="Partially updates an existing publication with new values.",
        tags=["Research - Publications"],
    ),
    destroy=extend_schema(
        summary="Delete a publication.",
        description="Deletes a single publication by its ID.",
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
