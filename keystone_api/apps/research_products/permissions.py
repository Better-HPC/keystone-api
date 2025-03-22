"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework import permissions

from apps.users.models import Team

__all__ = ['TeamMemberAll', 'TeamMemberReadTeamAdminWrite']


class CustomPermissionsBase(permissions.BasePermission):
    """Base manager class for common request processing logic."""

    def get_team(self, request) -> Team | None:
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


class TeamMemberAll(CustomPermissionsBase):
    """Permissions class providing read and write access to all users within the team."""

    def has_permission(self, request, view) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.method == 'TRACE' and not request.user.is_staff:
            return False

        team = self.get_team(request)
        return team is None or request.user in team.get_all_members()

    def has_object_permission(self, request, view, obj):
        """Return whether the incoming HTTP request has permission to access a database record."""

        return request.user in obj.team.get_all_members()


class TeamMemberReadTeamAdminWrite(CustomPermissionsBase):
    """Permissions class providing read access to regular users and read/write access to team admins."""

    def has_permission(self, request, view) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.method == 'TRACE' and not request.user.is_staff:
            return False

        team = self.get_team(request)
        return team is None or request.user in team.get_privileged_members()

    def has_object_permission(self, request, view, obj):
        """Return whether the incoming HTTP request has permission to access a database record."""

        read_only = request.method in permissions.SAFE_METHODS
        is_team_member = request.user in obj.team.get_all_members()
        is_team_admin = request.user in obj.team.get_privileged_members()
        return is_team_admin or (read_only and is_team_member)
