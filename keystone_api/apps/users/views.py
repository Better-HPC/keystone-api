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
        summary="Retrieve valid team role options",
        description="Retrieve valid team `role` options with human-readable labels.",
        tags=["Team Membership"],
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
        summary="List all team memberships",
        description="Retrieve all team membership accounts.",
        tags=["Team Membership"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a team membership",
        description="Retrieve a single team membership account by ID.",
        tags=["Team Membership"],
    ),
    create=extend_schema(
        summary="Create a team membership",
        description="Create a new team membership account.",
        tags=["Team Membership"],
    ),
    update=extend_schema(
        summary="Update a team membership",
        description="Replace an existing team membership account with new values.",
        tags=["Team Membership"],
    ),
    partial_update=extend_schema(
        summary="Partially update a team membership",
        description="Apply a partial update to an existing team membership account.",
        tags=["Team Membership"],
    ),
    destroy=extend_schema(
        summary="Delete a team membership",
        description="Delete a team membership account by ID.",
        tags=["Team Membership"],
    )
)
class MembershipViewSet(viewsets.ModelViewSet):
    """API endpoints for managing team membership."""

    queryset = Membership.objects.all()
    permission_classes = [IsAuthenticated, MembershipPermissions]
    serializer_class = MembershipSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all teams",
        description="Retrieve all teams visible to the current user.",
        tags=["Teams"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a team",
        description="Retrieve a single team by ID.",
        tags=["Teams"],
    ),
    create=extend_schema(
        summary="Create a team",
        description="Create a new team.",
        tags=["Teams"],
    ),
    update=extend_schema(
        summary="Update a team",
        description="Replace an existing team with new values.",
        tags=["Teams"],
    ),
    partial_update=extend_schema(
        summary="Partially update a team",
        description="Apply a partial update to an existing team.",
        tags=["Teams"],
    ),
    destroy=extend_schema(
        summary="Delete a team",
        description="Delete a team by ID.",
        tags=["Teams"],
    ),
)
class TeamViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user teams."""

    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated, TeamPermissions]
    serializer_class = TeamSerializer
    search_fields = ['name']


@extend_schema_view(
    list=extend_schema(
        summary="List all users",
        description="Retrieve all user accounts.",
        tags=["Users"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a user",
        description="Retrieve a single user account by ID.",
        tags=["Users"],
    ),
    create=extend_schema(
        summary="Create a user",
        description="Create a new user account.",
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Update a user",
        description="Replace an existing user account with new values.",
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Partially update a user",
        description="Apply a partial update to an existing user account.",
        tags=["Users"],
    ),
    destroy=extend_schema(
        summary="Delete a user",
        description="Delete a user account by ID.",
        tags=["Users"],
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user accounts."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, UserPermissions]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'department', 'role']

    def get_serializer_class(self) -> type[Serializer]:
        """Return the appropriate data serializer based on user roles/permissions."""

        # Allow staff users to read/write administrative fields
        if self.request.user.is_staff:
            return PrivilegedUserSerializer

        return RestrictedUserSerializer
