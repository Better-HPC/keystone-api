"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.mixins import UserScopedListMixin
from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'NotificationTypeChoicesView',
    'NotificationViewSet',
    'PreferenceViewSet',
]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve valid notification types",
        description="Retrieve valid notification types with human-readable labels.",
        tags=["Notifications"],
        responses=inline_serializer(
            name="NotificationTypeChoices",
            fields={k: serializers.CharField(default=v) for k, v in Notification.NotificationType.choices}
        )
    )
)
class NotificationTypeChoicesView(GenericAPIView):
    """API endpoints for exposing valid notification `type` values."""

    response_content = dict(Notification.NotificationType.choices)
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping values to human-readable names."""

        return Response(self.response_content)


@extend_schema_view(
    list=extend_schema(
        summary="List all notifications",
        description="Retrieve all notifications visible to the current user.",
        tags=["Notifications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a notification",
        description="Retrieve a single notification by ID.",
        tags=["Notifications"],
    ),
    partial_update=extend_schema(
        summary="Update a notification's read status",
        description="Update a notifications `read` status. All other fields are read only.",
        tags=["Notifications"],
    ),
)
class NotificationViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for retrieving user notifications."""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    search_fields = ['message', 'user__username']
    permission_classes = [IsAuthenticated, NotificationPermissions]
    http_method_names = ['get', 'head', 'options', 'patch']


@extend_schema_view(
    list=extend_schema(
        summary="List all notification preferences",
        description="Retrieve all notification preferences visible to the current user.",
        tags=["Notification Preferences"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a user's notification preferences",
        description="Retrieve a user's notification preference by ID.",
        tags=["Notification Preferences"],
    ),
    create=extend_schema(
        summary="Create a notification preference",
        description="Create a new notification preference.",
        tags=["Notification Preferences"],
    ),
    update=extend_schema(
        summary="Update a user's notification preferences",
        description="Replace a user's existing notification preference with new values.",
        tags=["Notification Preferences"],
    ),
    partial_update=extend_schema(
        summary="Partially update a user's notification preferences",
        description="Apply a partial update to a user's notification preference.",
        tags=["Notification Preferences"],
    ),
    destroy=extend_schema(
        summary="Delete a user's notification preferences",
        description="Delete a user's notification preference, and resort to default notification preferences.",
        tags=["Notification Preferences"],
    ),
)
class PreferenceViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing user notification preferences."""

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
