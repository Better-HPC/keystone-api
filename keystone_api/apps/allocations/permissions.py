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

__all__ = [
    'AllocationRequestPermissions',
    'ClusterPermissions',
    'StaffWriteMemberRead',
    'CommentPermissions',
]


class AllocationRequestPermissions(permissions.BasePermission):
    """RBAC permissions model for `AllocationRequest` objects.

    Permissions:
        - Grants read access to all team members.
        - Grants write access to team administrators.
        - Grants full access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff users are OK. Read operations are also OK.
        if request.user.is_staff or request.method in permissions.SAFE_METHODS:
            return True

        # To check write permissions we need to know what team the record belongs to.
        # Deny permissions if the team is not provided or does not exist.
        try:
            team_id = request.data.get('team', None)
            team = Team.objects.get(pk=team_id)

        except (Team.DoesNotExist, Exception):
            return False

        return request.user in team.get_privileged_members()

    def has_object_permission(self, request: Request, view: View, obj: AllocationRequest) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_team_member = request.user in obj.get_team().get_all_members()
        is_read_only = request.method in permissions.SAFE_METHODS

        return is_staff or (is_read_only and is_team_member)


class ClusterPermissions(permissions.BasePermission):
    """Grant read-only access to all authenticated users.

    Permissions:
        - Grants read access to all users.
        - Grants write access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        is_staff = request.user.is_staff
        is_read_only = request.method in permissions.SAFE_METHODS

        return is_staff or is_read_only


class CommentPermissions(permissions.BasePermission):
    """Grant write permissions to users in the same team as the requested object.

    Permissions:
        - Grants write access to team members and staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.user.is_staff or request.method in permissions.SAFE_METHODS:
            return True

        # To check write permissions we need to know what team the record belongs to.
        # Deny permissions if the team is not provided or does not exist.
        try:
            alloc_request_id = request.data.get('request', None)
            team = AllocationRequest.objects.get(pk=alloc_request_id).team

        except (Team.DoesNotExist, Exception):
            return False

        return request.user in team.get_all_members()

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        user_in_team = request.user in obj.get_team().get_all_members()
        return user_in_team or is_staff


class StaffWriteMemberRead(permissions.BasePermission):
    """Grant read access to users in to the same team as the requested object.

    Permissions:
        - Grants read access to users in the same team as the requested object.
        - Grants write access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_staff

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = request.user.is_staff
        is_read_only = request.method in permissions.SAFE_METHODS
        user_is_in_team = request.user in obj.get_team().get_all_members()

        return is_staff or (is_read_only and user_is_in_team)
