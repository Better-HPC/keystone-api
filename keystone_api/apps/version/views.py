"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['VersionView']


class VersionView(GenericAPIView):
    """API endpoints for exposing the API version."""

    permission_classes = []  # Public endpoint - no authentication required

    @extend_schema(
        auth=[],
        summary="Retrieve the application version number.",
        description="Returns the application version number as a plain text response.",
        tags=["Version"],
        responses={
            (200, 'text/plain'): OpenApiTypes.STR
        }
    )
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return the API version number."""

        return HttpResponse(settings.VERSION, content_type="text/plain")
