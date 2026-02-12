"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .mixins import TeamScopedListMixin
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
        tags=["Users - Team Membership"],
        summary="Retrieve valid team role options.",
        description="Returns valid choices for the team `role` field mapped to human-readable labels.",
        responses=inline_serializer(
            name="MembershipRoleChoices",
            fields={k: serializers.CharField(default=v) for k, v in Membership.Role.choices}
        )
    )
)
class MembershipRoleChoicesView(APIView):
    """API endpoints for exposing valid team `role` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(Membership.Role.choices)

    def get(self, request: Request) -> Response:
        """Return valid values for the team membership `role` field."""

        return Response(self.response_content)


@extend_schema_view(
    list=extend_schema(
        tags=["Users - Team Membership"],
        summary="List team memberships.",
        description="Returns a list of all team memberships.",
    ),
    retrieve=extend_schema(
        tags=["Users - Team Membership"],
        summary="Retrieve a team membership.",
        description="Returns a single team membership by ID.",
    ),
    create=extend_schema(
        tags=["Users - Team Membership"],
        summary="Create a team membership.",
        description=(
            "Creates a new team membership. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    update=extend_schema(
        tags=["Users - Team Membership"],
        summary="Update a team membership.",
        description=(
            "Replaces an existing team membership with new values. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    partial_update=extend_schema(
        tags=["Users - Team Membership"],
        summary="Partially update a team membership.",
        description=(
            "Partially updates an existing team membership with new values. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    destroy=extend_schema(
        tags=["Users - Team Membership"],
        summary="Delete a team membership.",
        description=(
            "Deletes a team membership by ID. "
            "Write access is granted to staff users, team owners/admins, "
            "and users deleting their own membership."
        ),
    )
)
class MembershipViewSet(viewsets.ModelViewSet):
    """API endpoints for managing team membership."""

    permission_classes = [IsAuthenticated, MembershipPermissions]
    serializer_class = MembershipSerializer
    search_fields = ['team__name', 'user__username']
    queryset = Membership.objects.prefetch_related(
        'history'
    ).select_related(
        'user',
        'team'
    )


@extend_schema_view(
    list=extend_schema(
        tags=["Users - Teams"],
        summary="List teams.",
        description=(
            "Returns a list of teams. "
            "Non-staff users are only returned teams they are a member of. Staff users are returned all teams."
        ),
    ),
    retrieve=extend_schema(
        tags=["Users - Teams"],
        summary="Retrieve a team.",
        description="Returns a single team by ID.",
    ),
    create=extend_schema(
        tags=["Users - Teams"],
        summary="Create a team.",
        description=(
            "Creates a new team. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    update=extend_schema(
        tags=["Users - Teams"],
        summary="Update a team.",
        description=(
            "Replaces an existing team with new values. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    partial_update=extend_schema(
        tags=["Users - Teams"],
        summary="Partially update a team.",
        description=(
            "Partially updates an existing team with new values. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
    destroy=extend_schema(
        tags=["Users - Teams"],
        summary="Delete a team.",
        description=(
            "Deletes a team by ID. "
            "Write access is granted to staff users and team owners/admins."
        ),
    ),
)
class TeamViewSet(TeamScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing user teams."""

    # Filter returned records using TeamScopedListMixin
    team_field = 'id'

    # General view configuration
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
        tags=["Users - Accounts"],
        summary="List user accounts.",
        description="Returns a list of all user accounts.",
    ),
    retrieve=extend_schema(
        tags=["Users - Accounts"],
        summary="Retrieve a user account.",
        description=(
            "Returns a single user account by ID. "
            "Staff users are returned all fields, including privileged values. "
            "Non-staff users are only returned restricted fields."
        ),
    ),
    create=extend_schema(
        tags=["Users - Accounts"],
        summary="Create a user account.",
        description=(
            "Creates a new user account. "
            "Only staff users may create new accounts."
        ),
    ),
    update=extend_schema(
        tags=["Users - Accounts"],
        summary="Update a user account.",
        description=(
            "Replaces an existing user account with new values. "
            "Write access is granted to staff users and the account owner. "
            "Non-staff users cannot modify privileged fields."
        ),
    ),
    partial_update=extend_schema(
        tags=["Users - Accounts"],
        summary="Partially update a user account.",
        description=(
            "Partially updates an existing user account with new values. "
            "Write access is granted to staff users and the account owner. "
            "Non-staff users cannot modify privileged fields."
        ),
    ),
    destroy=extend_schema(
        tags=["Users - Accounts"],
        summary="Delete a user.",
        description=(
            "Deletes a user account by ID. "
            "Write access is granted to staff users and the account owner."
        ),
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
