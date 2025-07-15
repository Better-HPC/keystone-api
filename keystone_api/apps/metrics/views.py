"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.http import HttpResponse
from django_prometheus import exports
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['MetricsView']


class MetricsView(GenericAPIView):
    """API endpoints for scraping application metrics."""

    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:  # pragma: no cover
        """Return prometheus metrics for monitoring the application."""

        return exports.ExportToDjangoView(request)
