"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

import asyncio
from typing import Collection

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from health_check.base import HealthCheckResult
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
            "Use the `format` path parameter to select the response format: "
            "omit for HTTP status only (200/500), `json` for JSON, or `prometheus` for Prometheus. "
            "Health checks are performed on demand and cached for 60 seconds."
        ),
        parameters=[
            OpenApiParameter(
                name='format',
                location='path',
                required=False,
                enum=['text', 'json', 'prometheus'],
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
    polling. The response format is selected via the `format` path parameter
    (e.g. ``/health/json/``); omitting it returns a bare 200/500 status code.
    """

    schema = AutoSchema()
    permission_classes = []
    checks = CHECKS


    async def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return a health response rendered fresh each time, but with check results cached."""

        cache_key = 'healthcheck_results'
        self.results = cache.get(cache_key)

        if self.results is None:
            self.results = await asyncio.gather(
                *(check.get_result() for check in self.get_checks())
            )

            cache.set(cache_key, self.results, CACHE_TIMEOUT)

        # Render into the requested format
        response_format = kwargs.get("format")
        match response_format:
            case "text":
                return self.render_to_response_text(status=200)

            case "json":
                return self.render_to_response_json(status=200)

            case "prometheus":
                return self.render_to_response_openmetrics()

        # No format requested - return a single status code reflecting overall health
        has_errors = any(result.error for result in self.results)
        status_code = 500 if has_errors else 200
        return HttpResponse(status=status_code)
