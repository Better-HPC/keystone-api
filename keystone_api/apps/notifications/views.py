"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'NotificationViewSet',
    'PreferenceViewSet',
]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns user notifications."""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    search_fields = ['message']
    permission_classes = [IsAuthenticated, NotificationOwnerReadOnly]

    def get_queryset(self) -> QuerySet:
        """Return a queryset of notifications for the requesting user."""

        return self.queryset.filter(user=self.request.user)


class PreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns user notification preferences."""

    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer
    permission_classes = [IsAuthenticated, PreferenceOwnerWrite]

    def get_queryset(self) -> QuerySet:
        """Return a queryset of notifications for the requesting user."""

        return self.queryset.filter(user=self.request.user)
