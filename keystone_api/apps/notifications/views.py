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
        summary="Retrieve valid notification types.",
        description="Returns valid choices for the notification `type` field mapped to human-readable labels.",
        tags=["Notifications - Notifications"],
        responses=inline_serializer(
            name="NotificationTypeChoices",
            fields={k: serializers.CharField(default=v) for k, v in Notification.NotificationType.choices}
        )
    )
)
class NotificationTypeChoicesView(GenericAPIView):
    """API endpoints for exposing valid notification `type` values."""

    permission_classes = [IsAuthenticated]
    response_content = dict(Notification.NotificationType.choices)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return a dictionary mapping values to human-readable names."""

        return Response(self.response_content)


@extend_schema_view(
    list=extend_schema(
        summary="List notifications.",
        description="Returns a filtered list of user notifications.",
        tags=["Notifications - Notifications"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a notification.",
        description="Returns a single notification by its ID.",
        tags=["Notifications - Notifications"],
    ),
    partial_update=extend_schema(
        summary="Partially update a notification.",
        description="Updates the `read` status of a notification.",
        tags=["Notifications - Notifications"],
    ),
)
class NotificationViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for retrieving user notifications."""

    permission_classes = [IsAuthenticated, NotificationPermissions]
    http_method_names = ['get', 'head', 'options', 'patch']
    search_fields = ['message', 'user__username']
    serializer_class = NotificationSerializer
    queryset = Notification.objects.select_related('user')


@extend_schema_view(
    list=extend_schema(
        summary="List notification preferences.",
        description="Returns a filtered list of notification preferences.",
        tags=["Notifications - Preferences"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a notification preference.",
        description="Returns a single notification preference by its ID.",
        tags=["Notifications - Preferences"],
    ),
    create=extend_schema(
        summary="Create a custom notification preference.",
        description="Creates a custom notification preference in lieu of application defaults.",
        tags=["Notifications - Preferences"],
    ),
    update=extend_schema(
        summary="Update a notification preference.",
        description="Replaces an existing notification preference with new values.",
        tags=["Notifications - Preferences"],
    ),
    partial_update=extend_schema(
        summary="Partially update a notification preference.",
        description="Partially updates an existing notification preference with new values.",
        tags=["Notifications - Preferences"],
    ),
    destroy=extend_schema(
        summary="Delete a notification preference.",
        description="Deletes a single notification preference by ID, restoring default settings.",
        tags=["Notifications - Preferences"],
    ),
)
class PreferenceViewSet(UserScopedListMixin, viewsets.ModelViewSet):
    """API endpoints for managing user notification preferences."""

    permission_classes = [IsAuthenticated, PreferencePermissions]
    search_fields = ['user__username']
    serializer_class = PreferenceSerializer
    queryset = Preference.objects.select_related('user')

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new `Preference` object.

        Defaults the `user` field to the authenticated user.
        """

        data = request.data.copy()
        data.setdefault('user', request.user.pk)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
