"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.serializers import RestrictedUserSerializer

__all__ = ['WhoAmIView']


class WhoAmIView(GenericAPIView):
    """Return user metadata for the currently authenticated user."""

    serializer_class = RestrictedUserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        """Return user metadata for the currently authenticated user.

        Returns:
            A 200 response with user data if authenticated, and a 401 response otherwise
        """

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
