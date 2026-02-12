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
        tags=["Notifications - Notifications"],
        summary="Retrieve valid notification types.",
        description="Returns valid choices for the notification `type` field mapped to human-readable labels.",
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
        tags=["Notifications - Notifications"],
        summary="List notifications.",
        description=(
            "Returns a list of user notifications. "
            "Non-staff users are only returned their own notifications. "
            "Staff users are returned all notifications."
        ),
    ),
    retrieve=extend_schema(
        tags=["Notifications - Notifications"],
        summary="Retrieve a notification.",
        description=(
            "Returns a single notification by its ID. "
            "Read and patch access is limited to the notification owner."
        ),
    ),
    partial_update=extend_schema(
        tags=["Notifications - Notifications"],
        summary="Partially update a notification.",
        description=(
            "Updates the `read` status of a notification. "
            "Patch access is limited to the notification owner."
        ),
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
        tags=["Notifications - Preferences"],
        summary="List notification preferences.",
        description=(
            "Returns a list of notification preferences. "
            "Non-staff users are only returned their own preferences. "
            "Staff users are returned all preferences."
        ),
    ),
    retrieve=extend_schema(
        tags=["Notifications - Preferences"],
        summary="Retrieve a notification preference.",
        description=(
            "Returns a single notification preference by its ID. "
            "Access is granted to staff users and the preference owner."
        ),
    ),
    create=extend_schema(
        tags=["Notifications - Preferences"],
        summary="Create a custom notification preference.",
        description=(
            "Creates a custom notification preference in lieu of application defaults. "
            "The `user` field defaults to the authenticated user if not specified. "
            "Access is granted to staff users and the preference owner."
        ),
    ),
    update=extend_schema(
        tags=["Notifications - Preferences"],
        summary="Update a notification preference.",
        description=(
            "Replaces an existing notification preference with new values. "
            "Access is granted to staff users and the preference owner."
        ),
    ),
    partial_update=extend_schema(
        tags=["Notifications - Preferences"],
        summary="Partially update a notification preference.",
        description=(
            "Partially updates an existing notification preference with new values. "
            "Access is granted to staff users and the preference owner."
        ),
    ),
    destroy=extend_schema(
        tags=["Notifications - Preferences"],
        summary="Delete a notification preference.",
        description=(
            "Deletes a single notification preference by ID, restoring default settings. "
            "Access is granted to staff users and the preference owner."
        ),
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
