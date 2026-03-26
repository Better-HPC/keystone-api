"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import *

__all__ = ['ConfigView']


@extend_schema_view(
    get=extend_schema(
        tags=["Configuration"],
        summary="Retrieve application configuration.",
        description=(
            "Returns application settings relevant to the frontend client. "
            "Includes application metadata, file upload constraints, feature flags, and session settings."
        ),
    )
)
class ConfigView(GenericAPIView):
    """API endpoint for exposing application configuration."""

    permission_classes = [IsAuthenticated]
    serializer_class = ConfigSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return the current application configuration."""

        data = {
            "version": settings.VERSION,
            "max_upload_size": settings.MAX_FILE_SIZE,
            "max_upload_count": settings.MAX_FILE_COUNT,
            "allowed_file_types": settings.ALLOWED_FILE_TYPES,
            "session_age": int(settings.SESSION_COOKIE_AGE),
        }

        serializer = self.serializer_class(data)
        return Response(serializer.data)
