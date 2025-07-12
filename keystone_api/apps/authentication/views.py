"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.serializers import RestrictedUserSerializer
from .serializers import *

__all__ = ['LoginView', 'LogoutView', 'WhoAmIView']


class LoginView(GenericAPIView):
    """Authenticate a user and start a new auth session."""

    permission_classes = []
    serializer_class = LoginSerializer

    @extend_schema(
        auth=[],
        summary="Authenticate a user and start a new session",
        description="Validate the provided credentials and start a new user session.",
        tags=["Authentication"],
        responses=RestrictedUserSerializer,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:  # pragma: no cover
        """Authenticate the user and establish a session.

        Returns:
            A 200 response with metadata for the authenticated user.
        """

        # Parse and validate the provided credentials
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        login(request, user)
        return Response(RestrictedUserSerializer(user).data)


class LogoutView(GenericAPIView):
    """Logout an authenticated user and terminate their session."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Logout an authenticated user",
        description="Logout an authenticated user and terminate their active session.",
        tags=["Authentication"]
    )
    def post(self, request: Request, *args, **kwargs) -> Response:  # pragma: no cover
        """Logout an authenticated user.

        Returns:
            An empty 200 response.
        """

        logout(request)
        return Response()


class WhoAmIView(GenericAPIView):
    """Return user metadata for the currently authenticated user."""

    serializer_class = RestrictedUserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve metadata for the currently authenticated user",
        description="Retrieve metadata for the currently authenticated user, including personal data and team memberships.",
        tags=["Authentication"],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return metadata for the currently authenticated user.

        Returns:
            A 200 response with metadata for the authenticated user.
        """

        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
