"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

from apps.notifications.models import Notification, Preference

__all__ = [
    "NotificationOwnerReadOnly",
    "PreferenceOwnerWrite"
]


class NotificationOwnerReadOnly(BasePermission):
    """Grant read-only access to users accessing their own notifications.

    Permissions:
        - Grants read access to users accessing their own notifications.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Allow access only for safe HTTP methods (GET, HEAD, OPTIONS)."""

        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj: Notification) -> bool:
        """Allow access only if the notification belongs to the requesting user."""

        if request.method in SAFE_METHODS:
            return obj.user == request.user

        return False


class PreferenceOwnerWrite(BasePermission):
    """Greats read/write access to users accessing their own preferences.

    Permissions:
        - Grants full permissions to users accessing their own preferences.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        if request.user.is_staff or request.method in SAFE_METHODS:
            return True

        # Users are only allowed to write to their own records
        user_id = request.data.get('user', None)
        return request.user.id == user_id

    def has_object_permission(self, request: Request, view: View, obj: Preference) -> bool:
        """Allow access only if the preference belongs to the requesting user."""

        return obj.user == request.user
