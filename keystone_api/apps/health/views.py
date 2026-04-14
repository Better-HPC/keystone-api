"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

import asyncio
from typing import Collection

import health_check
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from health_check.base import HealthCheck, HealthCheckResult
from health_check.views import HealthCheckView as BaseHealthCheckView
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from apps.health.checks import LDAPHealthCheck

__all__ = ['HealthCheckView']

# Cache duration for health check results in seconds
CACHE_TIMEOUT = 60

# The health checks to evaluate
CHECKS = [
    health_check.Mail(),
    health_check.Cache(),
    health_check.Database(),
    health_check.Storage(),
]

# Register the LDAP health check only when an LDAP server is configured
if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
    CHECKS.append(LDAPHealthCheck())


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
                enum=['json', 'prom'],
                description='The format of the returned health metrics.',
            )],
        responses={
            '200': inline_serializer('health_ok', fields=dict()),
            '500': inline_serializer('health_error', fields=dict()),
        },
    )
)
class HealthCheckView(GenericAPIView):
    """Health check view with response caching.

    Wraps the django-health-check `HealthCheckView` to cache responses for
    60 seconds, reducing load on downstream services during high-frequency
    polling. The response format is selected via the `format` path parameter
    (e.g. ``/health/json/``); omitting it returns a bare 200/500 status code.
    """

    schema = AutoSchema()
    permission_classes = []
    checks = CHECKS

    @staticmethod
    async def run_checks(checks: Collection[HealthCheck]) -> list[dict]:
        """Execute the provided health checks.

        Args:
            checks: The health checks to execute.

        Returns:
            Parsed health check results as a JSON dictionary.
        """

        results = await asyncio.gather(
            *(check.get_result() for check in checks)
        )

        return [
            {
                "check": result.check.__class__.__name__,
                "healthy": not bool(result.error),
                "error": str(result.error) if result.error else None,
                "time_taken": result.time_taken,
            }
            for result in results
        ]

    @staticmethod
    def render_to_custom_json(results: Collection[HealthCheckResult]) -> HttpResponse:
        """Return health check results as a JSON response."""

        return JsonResponse({'data': results}, content_type="application/json", status=200)

    @staticmethod
    def render_to_custom_prometheus(results: Collection[HealthCheckResult]) -> HttpResponse:
        """Return health check results in Prometheus format as a plain-text response."""

        lines = [
            "# HELP keystone_health_check_status Health check status (200 = healthy, 500 = unhealthy)",
            "# TYPE keystone_health_check_status gauge",
        ]

        for row in results:
            lines.append(f'keystone_health_check_status{{check="{row["check"]}"}} {row["healthy"]:d}')

        lines += [
            "",
            "# HELP keystone_health_check_eval_time_seconds Health check evaluation time in seconds",
            "# TYPE keystone_health_check_eval_time_seconds gauge",
        ]

        for row in results:
            lines.append(
                f'keystone_health_check_eval_time_seconds{{check="{row["check"]}"}} {row["time_taken"]:.6f}'
            )

        return HttpResponse(
            "\n".join(lines) + "\n",
            content_type="text/plain; charset=utf-8",
            status=200,
        )

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return a health response rendered fresh each time, but with check results cached."""

        cache_key = 'healthcheck_results'
        results = cache.get(cache_key)
        if results is None:
            results = async_to_sync(self.run_checks)(CHECKS)
            cache.set(cache_key, results, CACHE_TIMEOUT)

        # Render into the requested format
        response_format = kwargs.get("format")
        match response_format:
            case "json":
                return self.render_to_custom_json(results)

            case "prom":
                return self.render_to_custom_prometheus(results)

        # No format requested - return a single status code reflecting overall health
        has_errors = not all(result['healthy'] for result in results)
        status_code = 500 if has_errors else 200
        return HttpResponse(status=status_code)
