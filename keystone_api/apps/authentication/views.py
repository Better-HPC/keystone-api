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
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import RestrictedUserSerializer
from .serializers import *

__all__ = ['LoginView', 'LogoutView', 'WhoAmIView']


class LoginView(GenericAPIView):
    """Authenticate a user and start a new session."""

    permission_classes = []
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login user via session",
        description="Authenticate and login user using session-based authentication.",
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs) -> Response:
        """Authenticate the user and establish a session.

        Returns:
            A 200 response with metadata for the authenticated user.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        login(request, user)
        return Response(RestrictedUserSerializer(user).data)


class LogoutView(APIView):
    """Logout an authenticated user."""

    permission_classes = []

    def post(self, request, *args, **kwargs) -> Response:
        """Logout an authenticated user.

        Returns:
            A message confirming the logout result.
        """

        logout(request)
        return Response({'detail': 'Successfully logged out.'})


class WhoAmIView(GenericAPIView):
    """Return user metadata for the currently authenticated user."""

    serializer_class = RestrictedUserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve metadata for the currently authenticated user",
        description="Retrieve metadata for the currently authenticated user, including personal data and team memberships.",
        tags=["Authentication"],
    )
    def get(self, request, *args, **kwargs) -> Response:
        """Return metadata for the currently authenticated user.

        Returns:
            A 200 response with metadata for the authenticated user.
        """

        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
