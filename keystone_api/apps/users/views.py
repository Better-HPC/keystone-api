"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'TeamViewSet',
    'TeamMembershipRoleChoicesView',
    'TeamMembershipViewSet',
    'UserViewSet',
]


class TeamViewSet(viewsets.ModelViewSet):
    """Manage user teams."""

    queryset = Team.objects.all()
    permission_classes = [TeamPermissions]
    serializer_class = TeamSerializer
    search_fields = ['name']


class TeamMembershipRoleChoicesView(APIView):
    """Exposes valid values for the team membership `role` field."""

    _resp_body = dict(TeamMembership.Role.choices)

    @extend_schema(responses={'200': _resp_body})
    def get(self, request: Request) -> Response:
        """Return valid values for the team membership `role` field."""

        return Response(self._resp_body, status=status.HTTP_200_OK)


class TeamMembershipViewSet(viewsets.ModelViewSet):
    """Manage team membership."""

    queryset = TeamMembership.objects.all()
    permission_classes = [TeamMembershipPermissions]
    serializer_class = TeamMembershipSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Manage user account data."""

    queryset = User.objects.all()
    permission_classes = [UserPermissions]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'department', 'role']

    def get_serializer_class(self) -> type[Serializer]:
        """Return the appropriate data serializer based on user roles/permissions."""

        # Allow staff users to read/write administrative fields
        if self.request.user.is_staff:
            return PrivilegedUserSerializer

        return RestrictedUserSerializer
