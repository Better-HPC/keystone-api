"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from health_check.views import HealthCheckView as BaseHealthCheckView
from rest_framework.request import Request

from apps.health.backends import *

__all__ = ['HealthCheckView']

CACHE_TIMEOUT = 60  # seconds

CHECKS = [
    'health_check.Mail',
    'health_check.Cache',
    'health_check.Database',
    'health_check.Storage',
]

# Register the LDAP check only when an LDAP server is configured.
if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
    CHECKS.append(LDAPHealthCheck)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin - Health Checks"],
        auth=[],
        summary="Retrieve the current application health status.",
        description=(
            "Returns health check results in the requested format. "
            "Use the `format` query parameter to select the response format: "
            "omit for HTTP status only (200/500), `json` for JSON, or `openmetrics` for Prometheus. "
            "Health checks are performed on demand and cached for 60 seconds."
        ),
        parameters=[
            OpenApiParameter(
                name='format',
                location='query',
                required=False,
                enum=['json', 'openmetrics', 'text', 'rss', 'atom'],
                description='The format of the returned health metrics.',
            )],
        responses={
            '200': inline_serializer('health_ok', fields=dict()),
            '500': inline_serializer('health_error', fields=dict()),
        },
    )
)
class HealthCheckView(BaseHealthCheckView):
    """Health check view with response caching.

    Wraps the django-health-check `HealthCheckView` to cache responses for
    60 seconds, reducing load on downstream services during high-frequency
    polling. Format negotiation (JSON, OpenMetrics/Prometheus, text, RSS,
    Atom) is handled natively by the parent view via the `format` query
    parameter or `Accept` header.
    """

    schema = AutoSchema()
    permission_classes = []
    checks = CHECKS

    async def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return a cached health check response, running checks only when the cache is cold."""

        cache_key = 'healthcheck_cache'
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        response = await super().get(request, *args, **kwargs)
        cache.set(cache_key, response, CACHE_TIMEOUT)
        return response
