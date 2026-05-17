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

__all__ = ["MembershipPermissions", "TeamPermissions", "UserPermissions"]


class TeamPermissions(permissions.BasePermission):
    """RBAC permissions model for `Team` objects.

    Permissions:
        - Grants read access to all users.
        - Grants write access to staff and team administrators.
    """

    def has_object_permission(self, request: Request, view: View, obj: Team) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        # Staff have all permissions
        if request.user.is_staff:
            return True

        # Non-staff cannot access inactive teams
        if not obj.is_active:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.get_privileged_members().filter(pk=request.user.pk).exists()


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

        # Defer to object-level checks when no team is specified in the request body
        team_id = request.data.get("team")
        if team_id is None:
            return True

        # Write access to specific teams is based on the user's relation to the team
        try:
            team = Team.objects.get(id=team_id)

        except Team.DoesNotExist:
            return True  # Defer to object-level checks

        return team.get_privileged_members().filter(pk=request.user.pk).exists()

    def has_object_permission(self, request: Request, view: View, obj: Membership) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        # Allow users to remove their own membership
        if request.method == "DELETE" and obj.user == request.user:
            return True

        # Staff have all permissions
        if request.user.is_staff:
            return True

        # non-staff cannot access inactive teams
        if not obj.team.is_active:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.team.get_privileged_members().filter(pk=request.user.pk).exists()


class UserPermissions(permissions.BasePermission):
    """RBAC permissions model for `User` objects.

    Permissions:
        - Grants read access to all users.
        - Grants write access to all staff.
        - Grants write access to users modifying their own user record.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Only staff can create new records
        if getattr(view, "action", None) == "create":
            return request.user.is_staff

        # Defer to object based permissions for all other actions
        return True

    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_record_owner = (obj == request.user)
        is_readonly = request.method in permissions.SAFE_METHODS

        return is_readonly or is_record_owner or is_staff
