"""Custom permission objects used to manage access to HTTP endpoints.

Permission classes control access to API resources by determining user
privileges for different HTTP operations. They are applied at the view level,
enabling authentication and authorization to secure endpoints based on
predefined access rules.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS

__all__ = [
    "NotificationOwnerReadOnly",
    "PreferenceOwnerWrite"
]

class NotificationOwnerReadOnly(BasePermission):
    """Grant read-only access to users accessing their own notifications.

    Permissions:
        - Allows read access to notification recipients.
    """

    def has_permission(self, request, view):
        """Allow access only for safe HTTP methods (GET, HEAD, OPTIONS)."""

        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        """Allow access only if the notification belongs to the requesting user."""

        if request.method in SAFE_METHODS:
            return obj.user == request.user

        return False


class PreferenceOwnerWrite(BasePermission):
    """Greats read/write access to users accessing their own preferences.

    Permissions:
        - Grants full permissions to users accessing their own preferences.
    """

    def has_object_permission(self, request, view, obj):
        """Allow access only if the preference belongs to the requesting user."""

        return obj.user == request.user
