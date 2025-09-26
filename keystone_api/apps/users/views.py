"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'MembershipRoleChoicesView',
    'MembershipViewSet',
    'TeamViewSet',
    'UserViewSet',
]


@extend_schema_view(  # pragma: nocover
    get=extend_schema(
        summary="Retrieve valid team role options.",
        description="Returns valid choices for the team `role` field mapped to human-readable labels.",
        tags=["Users - Team Membership"],
        responses=inline_serializer(
            name="MembershipRoleChoices",
            fields={k: serializers.CharField(default=v) for k, v in Membership.Role.choices}
        )
    )
)
class MembershipRoleChoicesView(APIView):
    """API endpoints for exposing valid team `role` values."""

    _resp_body = dict(Membership.Role.choices)
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={'200': _resp_body})
    def get(self, request: Request) -> Response:
        """Return valid values for the team membership `role` field."""

        return Response(self._resp_body, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List team memberships.",
        description="Returns a filtered list of team memberships.",
        tags=["Users - Team Membership"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a team membership.",
        description="Returns a single team membership ID.",
        tags=["Users - Team Membership"],
    ),
    create=extend_schema(
        summary="Create a team membership.",
        description="Creates a new team membership.",
        tags=["Users - Team Membership"],
    ),
    update=extend_schema(
        summary="Update a team membership.",
        description="Replaces an existing team membership with new values.",
        tags=["Users - Team Membership"],
    ),
    partial_update=extend_schema(
        summary="Partially update a team membership.",
        description="Partially updates an existing team membership with new values.",
        tags=["Users - Team Membership"],
    ),
    destroy=extend_schema(
        summary="Delete a team membership.",
        description="Deletes a team membership by ID.",
        tags=["Users - Team Membership"],
    )
)
class MembershipViewSet(viewsets.ModelViewSet):
    """API endpoints for managing team membership."""

    permission_classes = [IsAuthenticated, MembershipPermissions]
    serializer_class = MembershipSerializer
    queryset = Membership.objects.prefetch_related(
        'history'
    ).select_related(
        'user',
        'team'
    )


@extend_schema_view(
    list=extend_schema(
        summary="List teams.",
        description="Returns a filtered list of user teams.",
        tags=["Users - Teams"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a team.",
        description="Returns a single team by ID.",
        tags=["Users - Teams"],
    ),
    create=extend_schema(
        summary="Create a team.",
        description="Creates a new team.",
        tags=["Users - Teams"],
    ),
    update=extend_schema(
        summary="Update a team.",
        description="Replaces an existing team with new values.",
        tags=["Users - Teams"],
    ),
    partial_update=extend_schema(
        summary="Partially update a team.",
        description="Partially updates an existing team with new values.",
        tags=["Users - Teams"],
    ),
    destroy=extend_schema(
        summary="Delete a team.",
        description="Deletes a team by ID.",
        tags=["Users - Teams"],
    ),
)
class TeamViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user teams."""

    permission_classes = [IsAuthenticated, TeamPermissions]
    serializer_class = TeamSerializer
    search_fields = ['name']
    queryset = Team.objects.prefetch_related(
        'membership__user',
        'users',
        'history'
    )


@extend_schema_view(
    list=extend_schema(
        summary="List user accounts.",
        description="Returns a filtered list of user accounts.",
        tags=["Users - Accounts"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a user account.",
        description="Returns a single user account by ID.",
        tags=["Users - Accounts"],
    ),
    create=extend_schema(
        summary="Create a user account.",
        description="Creates a new user account.",
        tags=["Users - Accounts"],
    ),
    update=extend_schema(
        summary="Update a user account.",
        description="Replaces an existing user account with new values.",
        tags=["Users - Accounts"],
    ),
    partial_update=extend_schema(
        summary="Partially update a user account.",
        description="Partially updates an existing user account with new values.",
        tags=["Users - Accounts"],
    ),
    destroy=extend_schema(
        summary="Delete a user.",
        description="Deletes a user account by ID.",
        tags=["Users - Accounts"],
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user accounts."""

    permission_classes = [IsAuthenticated, UserPermissions]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'department', 'role']
    queryset = User.objects.prefetch_related(
        'membership__team',
        'history'
    )

    def get_serializer_class(self) -> type[Serializer]:
        """Return the appropriate data serializer based on user roles/permissions."""

        # Allow staff users to read/write administrative fields
        if self.request.user.is_staff:
            return PrivilegedUserSerializer

        return RestrictedUserSerializer
