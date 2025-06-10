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

    def has_object_permission(self, request, view, obj: Notification) -> bool:
        """Allow access only if the notification belongs to the requesting user."""

        if request.method in SAFE_METHODS:
            return obj.user == request.user

        return False


class PreferenceOwnerWrite(BasePermission):
    """Greats read/write access to users accessing their own preferences.

    Permissions:
        - Grants full permissions to users accessing their own preferences.
        - Grants full permissions to staff users accessing any user's preferences.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """Return whether the request has permissions to access the requested resource."""

        # Only staff can create new records
        if getattr(view, 'action', None) == 'create' or request.method in SAFE_METHODS:
            return request.user.is_staff or request.method in SAFE_METHODS

        return True

    def has_object_permission(self, request: Request, view: View, obj: Preference) -> bool:
        """Allow access only if the preference belongs to the requesting user."""

        return request.user.is_staff or obj.user == request.user
