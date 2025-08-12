"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from django.http import HttpResponse
from django_prometheus import exports
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['MetricsView']


@extend_schema_view(
    get=extend_schema(
        auth=[],
        summary="Retrieve application metrics.",
        description="Returns Prometheus-formatted metrics for application monitoring.",
        tags=["Admin - Metrics"],
        responses={
            (200, 'text/plain'): OpenApiTypes.STR
        },
    )
)
class MetricsView(GenericAPIView):
    """API endpoints for scraping application metrics."""

    permission_classes = []

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:  # pragma: no cover
        """Return prometheus metrics for monitoring the application."""

        return exports.ExportToDjangoView(request)
