"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.http import HttpResponse
from django_prometheus import exports
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['MetricsView']


class MetricsView(GenericAPIView):
    """Endpoints for scraping application metrics."""

    permission_classes = []

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return prometheus metrics for monitoring the application."""

        return exports.ExportToDjangoView(request)
