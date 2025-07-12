"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['VersionView']


class VersionView(GenericAPIView):
    """API endpoints for exposing the API version."""

    permission_classes = []

    @extend_schema(
        auth=[],
        summary="Retrieve the application version number",
        description="Retrieve the application version number as a plain text response.",
        tags=["Application Version"],
        responses={
            (200, 'text/plain'): OpenApiTypes.STR
        },
        examples=[
            OpenApiExample(
                name="Version Number",
                media_type="text/plain",
                response_only=True,
                value="1.2.3"
            )
        ]
    )
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return the API version number."""

        return HttpResponse(settings.VERSION, content_type="text/plain")
