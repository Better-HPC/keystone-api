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
    'AllocationReviewPermissions',
    'ClusterPermissions',
    'CommentPermissions',
    'JobStatsPermissions',
    'RequestChildPermissions',
]


class PermissionUtils:
    """Common permission logic shared across permission classes."""

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
    def user_in_team(request: Request, obj: TeamModelInterface) -> bool:
        """Return whether the requested operation was made by a team member."""

        return request.user in obj.get_team().get_all_members()

    @staticmethod
    def user_is_team_admin(request: Request, team: Team) -> bool:
        """Return whether the requesting user is a privileged member of the given team."""

        return request.user in team.get_privileged_members()


class AllocationRequestPermissions(PermissionUtils, permissions.BasePermission):
    """RBAC permissions model for `AllocationRequest` objects.

    Permissions:
        - Grants read access to all team members.
        - Grants create access to team administrators.
        - Grants full access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff have all permissions.
        if self.user_is_staff(request):
            return True

        if self.is_read_only(request):
            return True

        # For create: only allow if the requesting user is an admin of the target team.
        # Deny creation if the target team cannot be resolved.
        if self.is_create(view):
            try:
                team_id = request.data.get('team')
                team = Team.objects.get(pk=team_id)

            except (Team.DoesNotExist, Exception):
                return False

            return self.user_is_team_admin(request, team)

        return False

    def has_object_permission(self, request: Request, view: View, obj: AllocationRequest) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = self.user_is_staff(request)
        is_read_only = self.is_read_only(request)
        is_team_member = self.user_in_team(request, obj)

        return is_staff or (is_read_only and is_team_member)


class AllocationReviewPermissions(PermissionUtils, permissions.BasePermission):
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


class RequestChildPermissions(PermissionUtils, permissions.BasePermission):
    """RBAC permissions model for models that are children of `AllocationRequest`.

    Applies to models where the team is resolved by walking through a related
    `AllocationRequest` instance, such as a `ResourceAllocation` or `Attachment`.

    Permissions:
        - Grants read access to all team members.
        - Grants create access to team administrators.
        - Grants full access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff have all permissions.
        if self.user_is_staff(request) or self.is_read_only(request):
            return True

        # For create: only allow if the requesting user is an admin of the target team.
        # Deny creation if the parent AllocationRequest cannot be resolved.
        if self.is_create(view):
            try:
                alloc_request_id = request.data.get('request')
                alloc_request = AllocationRequest.objects.select_related('team').get(pk=alloc_request_id)
                team = alloc_request.team

            except (AllocationRequest.DoesNotExist, Exception):
                return False

            return self.user_is_team_admin(request, team)

        return False

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        is_staff = self.user_is_staff(request)
        is_read_only = self.is_read_only(request)
        is_team_member = self.user_in_team(request, obj)

        return is_staff or (is_read_only and is_team_member)


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
        - Grants write access to staff users.
        - Grants write access to team members creating public comments.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Staff have all permissions.
        if self.user_is_staff(request) or self.is_read_only(request):
            return True

        # For create/update: only allow if user is in the target allocation's team.
        # Deny creation if allocation request can't be resolved.
        try:
            alloc_request_id = request.data.get('request')
            alloc_request = AllocationRequest.objects.get(pk=alloc_request_id)
            team = alloc_request.team

        except (Team.DoesNotExist, Exception):
            return not self.is_create(view)

        return not self.is_create(view) or request.user in team.get_all_members()

    def has_object_permission(self, request: Request, view: View, obj: Comment) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.user_is_staff(request) or (self.user_in_team(request, obj) and not obj.private)


class JobStatsPermissions(PermissionUtils, permissions.BasePermission):
    """Grant read-only access to users in the same team as the requested object.

    Permissions:
        - Grants read access to users in the same team as the requested object.
        - Grants read access to staff users.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        return not self.is_create(view)

    def has_object_permission(self, request: Request, view: View, obj: TeamModelInterface) -> bool:
        """Return whether the incoming HTTP request has permission to access a database record."""

        return self.is_read_only(request) and (self.user_is_staff(request) or self.user_in_team(request, obj))
