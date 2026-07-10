"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import QuerySet
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
    "MembershipRoleChoicesView",
    "MembershipViewSet",
    "TeamViewSet",
    "UserViewSet",
]


@extend_schema_view(
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
        description=(
            "Returns a list of team memberships. "
            "Non-staff users are only returned memberships for active teams. "
            "Staff users are returned all memberships."
        ),
    ),
    retrieve=extend_schema(
        tags=["Users - Team Membership"],
        summary="Retrieve a team membership.",
        description=(
            "Returns a single team membership by ID. "
            "Non-staff users can only retrieve memberships for active teams."
        ),
    ),
    create=extend_schema(
        tags=["Users - Team Membership"],
        summary="Create a team membership.",
        description=(
            "Creates a new team membership. "
            "Write access is granted to staff users and owners/admins of the target team."
        ),
    ),
    update=extend_schema(
        tags=["Users - Team Membership"],
        summary="Update a team membership.",
        description=(
            "Replaces an existing team membership with new values. "
            "Write access is granted to staff users and owners/admins of the target team."
        ),
    ),
    partial_update=extend_schema(
        tags=["Users - Team Membership"],
        summary="Partially update a team membership.",
        description=(
            "Partially updates an existing team membership with new values. "
            "Write access is granted to staff users and owners/admins of the target team."
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
    ),
)
class MembershipViewSet(viewsets.ModelViewSet):
    """API endpoints for managing team membership."""

    permission_classes = [IsAuthenticated, MembershipPermissions]
    serializer_class = MembershipSerializer
    search_fields = ["team__name", "user__username", "user__first_name", "user__last_name"]
    queryset = Membership.objects.prefetch_related(
        "history"
    ).select_related(
        "team",
        "user",
    )

    def get_queryset(self) -> QuerySet:
        """Return the appropriate queryset for an incoming request.

        Staff users are returned a query including all records.
        Non-staff are limited to memberships where the team and user are both active.
        """

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(team__is_active=True, user__is_active=True)

        return queryset


@extend_schema_view(
    list=extend_schema(
        tags=["Users - Teams"],
        summary="List teams.",
        description=(
            "Returns a list of teams. "
            "Non-staff users are only returned active teams. "
            "Staff users are returned all teams."
        ),
    ),
    retrieve=extend_schema(
        tags=["Users - Teams"],
        summary="Retrieve a team.",
        description=(
            "Returns a single team by ID. "
            "Non-staff users can only retrieve active teams."
        ),
    ),
    create=extend_schema(
        tags=["Users - Teams"],
        summary="Create a team.",
        description=(
            "Creates a new team. "
            "All authenticated users can only create active teams. "
            "Inactive teams can only be created by staff users."
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
    team_field = "id"

    # General view configuration
    permission_classes = [IsAuthenticated, TeamPermissions]
    serializer_class = TeamSerializer
    search_fields = ["name"]
    queryset = Team.objects.prefetch_related(
        "history",
        "membership__user",
        "users",
    )

    def get_serializer_class(self) -> type[Serializer]:
        """Return the appropriate data serializer class for an incoming request.

        Update operations are returned the `TeamUpdateSerializer` class.
        All other operations are returned the `TeamSerializer` class.
        """

        if self.action in ("update", "partial_update"):
            return TeamUpdateSerializer

        return TeamSerializer

    def get_queryset(self) -> QuerySet:
        """Return the appropriate queryset for an incoming request.

        Staff users are returned a query including all records.
        Non-staff are limited to active team records only.
        """

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset


@extend_schema_view(
    list=extend_schema(
        tags=["Users - Accounts"],
        summary="List user accounts.",
        description=(
            "Returns a list of all user accounts. "
            "Staff users are returned records with all fields, including privileged values. "
            "Non-staff users are only returned restricted fields."
        ),
    ),
    retrieve=extend_schema(
        tags=["Users - Accounts"],
        summary="Retrieve a user account.",
        description=(
            "Returns a single user account by ID. "
            "Staff users are returned all record fields, including privileged values. "
            "Non-staff users are only returned restricted fields."
        ),
    ),
    create=extend_schema(
        tags=["Users - Accounts"],
        summary="Create a user account.",
        request=PrivilegedUserSerializer,
        description=(
            "Creates a new user account. "
            "Only staff users may create new accounts."
        ),
    ),
    update=extend_schema(
        tags=["Users - Accounts"],
        summary="Update a user account.",
        request=PrivilegedUserSerializer,
        description=(
            "Replaces an existing user account with new values. "
            "Write access is granted to staff users and the account owner. "
            "Non-staff users cannot modify privileged fields."
        ),
    ),
    partial_update=extend_schema(
        tags=["Users - Accounts"],
        summary="Partially update a user account.",
        request=PrivilegedUserSerializer,
        description=(
            "Partially updates an existing user account with new values. "
            "Write access is granted to staff users and the account owner. "
            "Non-staff users cannot modify privileged fields."
        ),
    ),
    destroy=extend_schema(
        tags=["Users - Accounts"],
        summary="Delete a user account.",
        request=PrivilegedUserSerializer,
        description=(
            "Deletes a user account by ID. "
            "Write access is granted to staff users and the account owner."
        ),
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user accounts."""

    permission_classes = [IsAuthenticated, UserPermissions]
    search_fields = ["username", "first_name", "last_name", "email", "department", "role"]
    queryset = User.objects.prefetch_related(
        "groups",
        "history",
        "membership__team",
        "user_permissions",
    )

    def get_serializer_class(self) -> type[Serializer]:
        """Return the appropriate data serializer class for an incoming request.

         Staff users are returned a `PrivilegedUserSerializer` class.
         Non-staff users are returned a `RestrictedUserSerializer` class.
         """

        # Allow staff users to read/write administrative fields
        if self.request.user.is_staff:
            return PrivilegedUserSerializer

        return RestrictedUserSerializer

    def get_queryset(self) -> QuerySet:
        """Return the appropriate queryset for an incoming request.

        Staff users are returned a query including all records.
        Non-staff are limited to active user records only.
        """

        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset
