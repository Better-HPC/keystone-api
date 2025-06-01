"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

__all__ = ["IsAdminRead"]


class IsAdminRead(permissions.BasePermission):
    """Restricts read access to administrators without restricting other actions.

    Permissions:
        - Grants read access administrators.
        - Does not affect write operations.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        return request.user.is_staff or request.method not in permissions.SAFE_METHODS
