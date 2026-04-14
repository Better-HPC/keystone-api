"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

import asyncio
import json
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

    async def run_checks(self) -> list[dict]:

        results = await asyncio.gather(
            *(check.get_result() for check in self.get_checks())
        )

        return [
            {
                "check": repr(result.check),
                "healthy": not bool(result.error),
                "error": str(result.error) if result.error else None,
                "time_taken": result.time_taken,
            }
            for result in results
        ]

    def render_to_custom_json(self, results: Collection[HealthCheckResult]) -> HttpResponse:
        """Return a JSON response with health check results."""

        payload = {
            "healthy": all(row["healthy"] for row in results),
            "checks": results,
        }

        return HttpResponse(
            json.dumps(payload, indent=2),
            content_type="application/json",
            status=200,
        )

    def render_to_custom_text(self, results: Collection[HealthCheckResult]) -> HttpResponse:
        """Return a plain-text response with health check results."""

        lines = []
        for row in results:
            status = "OK" if row["healthy"] else f"ERROR: {row['error']}"
            lines.append(f"{row['check']}: {status} ({row['time_taken']:.6f}s)")

        overall = "OK" if all(row["healthy"] for row in results) else "ERROR"
        lines.append(f"\nOverall: {overall}")

        return HttpResponse(
            "\n".join(lines) + "\n",
            content_type="text/plain; charset=utf-8",
            status=200,
        )

    def render_to_custom_prometheus(self, results: Collection[HealthCheckResult]) -> HttpResponse:
        """Return an OpenMetrics response with health check results."""

        lines = [
            "# HELP keystone_health_check_status Health check status (1 = healthy, 0 = unhealthy)",
            "# TYPE keystone_health_check_status gauge",
        ]

        for row in results:
            safe_label = self._escape_openmetrics_label_value(row["check"])
            lines.append(f'keystone_health_check_status{{check="{safe_label}"}} {row["healthy"]:d}')

        lines += [
            "",
            "# HELP keystone_health_check_response_time_seconds Health check response time in seconds",
            "# TYPE keystone_health_check_response_time_seconds gauge",
        ]

        for row in results:
            safe_label = self._escape_openmetrics_label_value(row["check"])
            lines.append(
                f'keystone_health_check_response_time_seconds{{check="{safe_label}"}} {row["time_taken"]:.6f}'
            )

        overall_healthy = all(row["healthy"] for row in results)
        lines += [
            "",
            "# HELP keystone_health_check_overall_status Overall health check status (1 = all healthy, 0 = at least one unhealthy)",
            "# TYPE keystone_health_check_overall_status gauge",
            f"keystone_health_check_overall_status {overall_healthy:d}",
            "# EOF",
        ]

        return HttpResponse(
            "\n".join(lines) + "\n",
            content_type="application/openmetrics-text; version=1.0.0; charset=utf-8",
            status=200,
        )

    async def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Return a health response rendered fresh each time, but with check results cached."""

        cache_key = 'healthcheck_results'
        results = cache.get(cache_key)
        if results is None:
            results = await self.run_checks()
            cache.set(cache_key, results, CACHE_TIMEOUT)

        # Render into the requested format
        response_format = kwargs.get("format")
        match response_format:
            case "text":
                return self.render_to_custom_text(results)

            case "json":
                return self.render_to_custom_json(results)

            case "prometheus":
                return self.render_to_custom_prometheus(results)

        # No format requested - return a single status code reflecting overall health
        has_errors = not all(result['healthy'] for result in results)
        status_code = 500 if has_errors else 200
        return HttpResponse(status=status_code)
