"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.mixins import UserScopedListMixin
from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'NotificationViewSet',
    'PreferenceViewSet',
]


class NotificationViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """Returns user notifications."""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    search_fields = ['message', 'user__username']
    permission_classes = [IsAuthenticated, NotificationPermissions]
    http_method_names = ['get', 'head', 'options', 'patch']


class PreferenceViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """Returns user notification preferences."""

    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer
    search_fields = ['user__username']
    permission_classes = [IsAuthenticated, PreferencePermissions]

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new `Preference` object."""

        data = request.data.copy()
        data.setdefault('user', request.user.pk)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
