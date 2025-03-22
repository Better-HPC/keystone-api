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

__all__ = ['TeamPermissions', 'TeamMembershipPermissions', 'UserPermissions']


class TeamPermissions(permissions.BasePermission):
    """Permissions model for `Team` objects.

    Grants read-only access to all authenticated users.
    Write access is granted to staff and team administrators.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        return request.user.is_authenticated

    def has_object_permission(self, request: Request, view: View, obj: Team):
        """Return whether the incoming HTTP request has permission to access a database record."""

        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Update permissions are only allowed for staff and team admins
        return request.user.is_staff or request.user in obj.get_privileged_members()


class TeamMembershipPermissions(TeamPermissions):
    """Permissions model for `TeamMembership` objects.

    Grants read-only access to all authenticated users.
    Write access is granted to staff and team administrators.
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
            return request.user.is_authenticated

    def has_object_permission(self, request: Request, view: View, obj: TeamMembership):
        """Return whether the incoming HTTP request has permission to access a database record."""

        if request.user.is_staff or request.method in permissions.SAFE_METHODS:
            return True

        # Users can delete their own group membership
        if request.method == "DELETE" and obj.user == request.user:
            return True

        return request.user in obj.team.get_privileged_members()


class UserPermissions(permissions.BasePermission):
    """Permissions model for `User` objects.

    Grants read-only permissions to everyone and limits write access to staff and
    to user's accessing their own user record.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.method == 'POST':
            return request.user.is_staff

        return request.user.is_authenticated

    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        # Write operations are restricted to staff and user's modifying their own data
        is_record_owner = obj == request.user
        is_readonly = request.method in permissions.SAFE_METHODS
        return is_readonly or is_record_owner or request.user.is_staff
