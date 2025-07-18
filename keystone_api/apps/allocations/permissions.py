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
    'CommentPermissions',
    'MemberReadOnly',
    'StaffWriteMemberRead',
]


class PermissionUtils:
    """Common permission logic."""

    @staticmethod
    def is_create(view: View) -> bool:
        """Return whether the requested operation creates a new record."""

        return getattr(view, 'action', None) == 'create'

    @staticmethod
    def is_read_only(request: Request) -> bool:
        """Return whether the requested operation is read-only."""

        return request.method in permissions.SAFE_METHODS

    @staticmethod
    def user_is_staff(request: Request) -> bool:
        """Return whether the requested operation was made by a staff user."""

        return request.user and request.user.is_staff

    @staticmethod
    def user_in_team(request, obj) -> bool:
        """Return whether the requested operation was made by a team member."""

        return request.user in obj.get_team().get_all_members()


class AllocationRequestPermissions(PermissionUtils, permissions.BasePermission):
    """RBAC permissions model for `AllocationRequest` objects.

    Permissions:
        - Grants read access to all team members.
        - Grants write access to team administrators.
        - Grants full access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff users are OK. Read operations are also OK.
        if self.user_is_staff(request) or self.is_read_only(request):
            return True

        try:
            team_id = request.data.get('team')
            team = Team.objects.get(pk=team_id)

        except (Team.DoesNotExist, Exception):
            return not self.is_create(view)

        return not self.is_create(view) or request.user in team.get_privileged_members()

    def has_object_permission(self, request: Request, view: View, obj: AllocationRequest) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.user_is_staff(request) or (self.is_read_only(request) and self.user_in_team(request, obj))


class ClusterPermissions(PermissionUtils, permissions.BasePermission):
    """Grant read-only access to all authenticated users.

    Permissions:
        - Grants read access to all users.
        - Grants write access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Only staff can create new records.
        return self.user_is_staff(request) or not self.is_create(view)

    def has_object_permission(self, request: Request, view: View, obj: Cluster) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.user_is_staff(request) or self.is_read_only(request)


class CommentPermissions(PermissionUtils, permissions.BasePermission):
    """Grant write permissions to users in the same team as the requested object.

    Permissions:
        - Grants write access to team members and staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if self.user_is_staff(request) or self.is_read_only(request):
            return True

        try:
            alloc_request_id = request.data.get('request')
            alloc_request = AllocationRequest.objects.get(pk=alloc_request_id)
            team = alloc_request.team

        except (Team.DoesNotExist, Exception):
            return not self.is_create(view)

        return not self.is_create(view) or request.user in team.get_all_members()

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.user_is_staff(request) or self.user_in_team(request, obj)


class MemberReadOnly(PermissionUtils, permissions.BasePermission):
    """Grant read-only access to users in the same team as the requested object.

    Permissions:
        - Grants read access to users in the same team as the requested object.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        return not self.is_create(view)

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.is_read_only(request) and (self.user_is_staff(request) or self.user_in_team(request, obj))


class StaffWriteMemberRead(PermissionUtils, permissions.BasePermission):
    """Grant read access to users in the same team as the requested object and write access to staff.

    Permissions:
        - Grants read access to users in the same team as the requested object.
        - Grants write access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Only staff can create new records.
        return self.user_is_staff(request) or not self.is_create(view)

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.user_is_staff(request) or (self.is_read_only(request) and self.user_in_team(request, obj))
