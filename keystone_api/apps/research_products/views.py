"""Application logic for rendering responses to HTTP requests.

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

__all__ = ["GrantViewSet", "PublicationViewSet"]


@extend_schema_view(
    list=extend_schema(
        tags=["Research - Grants"],
        summary="List funding grants.",
        description=(
            "Returns a list of funding grants. "
            "Non-staff users are only returned grants for teams where they hold membership. "
            "Staff users are returned all grants."
        ),
    ),
    retrieve=extend_schema(
        tags=["Research - Grants"],
        summary="Retrieve a funding grant.",
        description=(
            "Returns a single funding grant by ID. "
            "Non-staff users can only retrieve grants for teams where they hold membership."
        ),
    ),
    create=extend_schema(
        tags=["Research - Grants"],
        summary="Create a funding grant.",
        description=(
            "Creates a new funding grant. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    update=extend_schema(
        tags=["Research - Grants"],
        summary="Update a funding grant.",
        description=(
            "Replaces an existing funding grant with new values. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    partial_update=extend_schema(
        tags=["Research - Grants"],
        summary="Partially update a funding grant.",
        description=(
            "Partially updates an existing funding grant with new values. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    destroy=extend_schema(
        tags=["Research - Grants"],
        summary="Delete a funding grant.",
        description=(
            "Deletes a funding grant by ID. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
)
class GrantViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing funding awards and grant information."""

    model = Grant
    team_field = "team"

    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]
    search_fields = ["title", "agency", "team__name"]
    serializer_class = GrantSerializer
    queryset = Grant.objects.prefetch_related(
        "history",
        "team",
    ).all()


@extend_schema_view(
    list=extend_schema(
        tags=["Research - Publications"],
        summary="List publications.",
        description=(
            "Returns a list of publications. "
            "Non-staff users are only returned publications for teams where they hold membership. "
            "Staff users are returned all publications."
        ),
    ),
    retrieve=extend_schema(
        tags=["Research - Publications"],
        summary="Retrieve a publication.",
        description=(
            "Returns a single publication by ID. "
            "Non-staff users can only retrieve publications for teams where they hold membership."
        ),
    ),
    create=extend_schema(
        tags=["Research - Publications"],
        summary="Create a publication.",
        description=(
            "Creates a new publication. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    update=extend_schema(
        tags=["Research - Publications"],
        summary="Update a publication.",
        description=(
            "Replaces an existing publication with new values. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    partial_update=extend_schema(
        tags=["Research - Publications"],
        summary="Partially update a publication.",
        description=(
            "Partially updates an existing publication with new values. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
    destroy=extend_schema(
        tags=["Research - Publications"],
        summary="Delete a publication.",
        description=(
            "Deletes a publication by ID. "
            "Write access is granted to staff users and members of the target team."
        ),
    ),
)
class PublicationViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing research publications."""

    model = Publication
    team_field = "team"

    permission_classes = [IsAuthenticated, IsAdminUser | IsTeamMember]
    search_fields = ["title", "abstract", "journal", "doi", "team__name"]
    serializer_class = PublicationSerializer
    queryset = Publication.objects.prefetch_related(
        "history",
        "team",
    ).all()
