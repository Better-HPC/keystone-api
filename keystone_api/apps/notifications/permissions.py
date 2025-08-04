"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

from .models import *

__all__ = [
    "NotificationPermissions",
    "PreferencePermissions"
]


class NotificationPermissions(BasePermission):
    """Grant read-only access to users accessing their own notifications.

    Permissions:
        - Grants read and patch access to users accessing their own notifications.
    """

    _allowed_methods = SAFE_METHODS + ('PATCH',)

    def has_object_permission(self, request, view, obj: Notification) -> bool:
        """Allow access only if the notification belongs to the requesting user."""

        if request.method in self._allowed_methods:
            return obj.user == request.user

        return False


class PreferencePermissions(BasePermission):
    """Greats read/write access to users accessing their own preferences.

    Permissions:
        - Grants full permissions to users accessing their own preferences.
        - Grants full permissions to staff users accessing any user's preferences.
    """

    def has_object_permission(self, request: Request, view: View, obj: Preference) -> bool:
        """Allow access only if the preference belongs to the requesting user."""

        return request.user.is_staff or obj.user == request.user
