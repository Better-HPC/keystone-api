"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

from .models import *

__all__ = ['TeamPermissions', 'MembershipPermissions', 'UserPermissions']


class TeamPermissions(permissions.BasePermission):
    """RBAC permissions model for `Team` objects.

    Permissions:
        - Grants read access to all users.
        - Grants write access to staff and team administrators.
    """

    def has_object_permission(self, request: Request, view: View, obj: Team) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_readonly = request.method in permissions.SAFE_METHODS
        is_team_admin = request.user in obj.get_privileged_members()

        return is_readonly or is_team_admin or is_staff


class MembershipPermissions(TeamPermissions):
    """RBAC permissions model for `Membership` objects.

    Permissions:
        - Grants read access to all users.
        - Grants write access to staff and team administrators.
        - Grants write access to users deleting their own membership records.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff have all permissions
        if request.user.is_staff:
            return True

        # Write access to specific teams is based on the user's relation to the team
        try:
            team = Team.objects.get(id=request.data.get('team'))
            return request.user in team.get_privileged_members()

        except Team.DoesNotExist:
            return True

    def has_object_permission(self, request: Request, view: View, obj: Membership) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        # Allow users to remove their own membership
        if request.method == "DELETE" and obj.user == request.user:
            return True

        is_staff = request.user.is_staff
        is_readonly = request.method in permissions.SAFE_METHODS
        is_team_admin = request.user in obj.team.get_privileged_members()

        return is_readonly or is_team_admin or is_staff


class UserPermissions(permissions.BasePermission):
    """RBAC permissions model for `User` objects.

    Permissions:
        - Grants read access to all users.
        - Grants write to all staff.
        - Grants write access to users modifying their own user record.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Only staff can create new records
        if getattr(view, 'action', None) == 'create':
            return request.user.is_staff

        # Defer to object based permissions for all other actions
        return True

    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_record_owner = (obj == request.user)
        is_readonly = request.method in permissions.SAFE_METHODS

        return is_readonly or is_record_owner or is_staff
