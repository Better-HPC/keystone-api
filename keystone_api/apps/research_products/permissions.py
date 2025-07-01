"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

from apps.users.models import Team
from .models import *

__all__ = ['IsTeamMember']


class IsTeamMember(permissions.BasePermission):
    """Team based record permissions.

    Permissions:
        - Grants read and write access to team members.
        - Grants read and write access to staff.
    """

    def get_team(self, request: Request) -> Team | None:
        """Return the team indicated in the `team` field of an incoming request.

        Args:
            request: The HTTP request

        Returns:
            The team or None
        """

        try:
            team_id = request.data.get('team', None)
            return Team.objects.get(pk=team_id)

        except Team.DoesNotExist:
            return None

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        team = self.get_team(request)
        return team is None or request.user in team.get_all_members()

    def has_object_permission(self, request: Request, view: View, obj: Publication) -> None:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_team_member = request.user in obj.team.get_all_members()
        return is_team_member or is_staff
