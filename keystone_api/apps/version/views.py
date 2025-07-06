"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['VersionView']


class VersionView(GenericAPIView):
    """Endpoints for exposing the API version."""

    _resp_body = {'version': settings.VERSION}
    permission_classes = []

    @extend_schema(
        summary="Retrieve the application version number",
        description="Retrieve the application version number.",
        responses={'200': _resp_body},
        tags=["Application Version"],
    )
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return the API version number."""

        return HttpResponse(self._resp_body)
