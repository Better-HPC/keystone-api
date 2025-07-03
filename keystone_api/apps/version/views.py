"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.conf import settings
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['VersionView']


class VersionView(GenericAPIView):
    """Endpoints for exposing the API version."""

    permission_classes = []

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return the API version number."""

        return HttpResponse(settings.VERSION)
