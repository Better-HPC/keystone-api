"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

import asyncio

import health_check
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiExample, OpenApiResponse
from health_check.base import HealthCheck
from health_check.contrib.celery import Ping
from health_check.contrib.redis import Redis
from redis.asyncio import Redis as RedisClient
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from apps.health.checks import LDAPHealthCheck

__all__ = ['HealthCheckView', 'HealthCheckJsonView', 'HealthCheckPrometheusView']

# Cache duration for health check results in seconds
CACHE_TIMEOUT = 60

# Mapping of human-friendly names to health check instances
CHECKS: dict[str, HealthCheck] = {
    "SMTP": health_check.Mail(),
    "Database": health_check.Database(),
    "Storage": health_check.Storage(),
    "Redis": Redis(client_factory=lambda: RedisClient.from_url(settings.REDIS_URL)),
    "Celery": Ping(),
}

# Register the LDAP health check only when an LDAP server is configured
if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
    CHECKS["LDAP"] = LDAPHealthCheck()


class BaseHealthCheckView(GenericAPIView):
    """Base view providing shared health check execution and caching logic.

    Subclasses must implement `render` to format the cached results into the
    appropriate HTTP response for their endpoint.
    """

    schema = AutoSchema()
    permission_classes = []
    checks = CHECKS

    @staticmethod
    async def run_checks(checks: dict[str, HealthCheck]) -> list[dict]:
        """Execute the provided health checks.

        Args:
            checks: Mapping of human-friendly names to health check instances.

        Returns:
            Parsed health check results as a JSON serializable list.
        """

        results = await asyncio.gather(
            *(check.get_result() for check in checks.values())
        )

        return [
            {
                "check": name,
                "healthy": not bool(result.error),
                "error": str(result.error) if result.error else None,
                "time_taken": result.time_taken,
            }
            for name, result in zip(checks.keys(), results)
        ]

    @staticmethod
    def get_cached_results() -> list[dict]:
        """Return cached health check results, running checks if the cache is cold."""

        cache_key = 'healthcheck_results'
        results = cache.get(cache_key)
        if results is None:
            results = async_to_sync(BaseHealthCheckView.run_checks)(CHECKS)
            cache.set(cache_key, results, CACHE_TIMEOUT)

        return results

    def render_response(self, results: list[dict]) -> HttpResponse:
        """Render health check results into an HTTP response.

        Args:
            results: Parsed health check results as returned by ``run_checks``.

        Returns:
            An HTTP response in the format appropriate for the subclass.
        """

        raise NotImplementedError

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Handle an incoming HTTP GET request.

        Evaluate system health checks, using cached results if possible, and
        return the rendered results.
        """

        return self.render_response(self.get_cached_results())


@extend_schema_view(
    get=extend_schema(
        tags=["Admin - Health Checks"],
        auth=[],
        summary="Retrieve the current application health status.",
        description=(
            "Returns a 200 status if all application health checks pass and a 500 status otherwise. "
            "Health checks are performed on demand and cached for 60 seconds. "
        ),
        responses={
            '200': inline_serializer('health_ok', fields=dict()),
            '500': inline_serializer('health_error', fields=dict()),
        }
    )
)
class HealthCheckView(BaseHealthCheckView):
    """Returns a bare `200` or 500` status code reflecting overall health."""

    def render_response(self, results: list[dict]) -> HttpResponse:
        """Return an empty HTTP response with a status code reflecting overall health.

        Args:
            results: The health check results to render.

        Returns:
            An empty HTTP response with a `200` or 500` status code.
        """

        has_errors = not all(result['healthy'] for result in results)
        return HttpResponse(status=500 if has_errors else 200)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin - Health Checks"],
        auth=[],
        summary="Retrieve health status as JSON.",
        description=(
            "Returns individual health check results in JSON format. "
            "Health checks are performed on demand and cached for 60 seconds. "
            "A `200` status code is returned regardless of whether individual health checks are passing. "
        ),
        responses={
            '200': OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Health check results.',
                examples=[
                    OpenApiExample(
                        'JSON response',
                        response_only=True,
                        value={'data': [
                            {"check": "Storage", "healthy": True, "error": None, "time_taken": 0.012},
                            {"check": "Celery", "healthy": False, "error": "Celery workers unavailable", "time_taken": 1.001},
                        ]},
                    ),
                ],
            ),
        },
    )
)
class HealthCheckJsonView(BaseHealthCheckView):
    """Returns health check results as a JSON response."""

    def render_response(self, results: list[dict]) -> HttpResponse:
        """Render health check results into a JSON response.

        Args:
            results: The health check results to render.

        Returns:
            An HTTP response with health check results in JSON format.
        """

        return JsonResponse({'data': results}, content_type="application/json", status=200)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin - Health Checks"],
        auth=[],
        summary="Retrieve health check results in Prometheus format.",
        description=(
            "Returns individual health check results in Prometheus format. "
            "Health checks are performed on demand and cached for 60 seconds. "
            "A `200` status code is returned regardless of whether individual health checks are passing. "
        ),
        responses={
            '200': OpenApiResponse(
                response=OpenApiTypes.STR,
                description='Prometheus plain-text metrics.',
                examples=[
                    OpenApiExample(
                        'Prometheus response',
                        response_only=True,
                        value=(
                                "# HELP keystone_health_check_status Health check status (200 = healthy, 500 = unhealthy)\n"
                                "# TYPE keystone_health_check_status gauge\nkeystone_health_check_status{check=\"Storage\"} 200\n"
                                "keystone_health_check_status{check=\"Celery\"} 500\n\n"
                                "# HELP keystone_health_check_eval_time_seconds Health check evaluation time in seconds\n"
                                "# TYPE keystone_health_check_eval_time_seconds gauge\nkeystone_health_check_eval_time_seconds{check=\"Storage\"} 0.008000\n"
                                "keystone_health_check_eval_time_seconds{check=\"Celery\"} 1.001000",
                        )
                    ),
                ],
            ),
        },
    )
)
class HealthCheckPrometheusView(BaseHealthCheckView):
    """Returns health check results in Prometheus text format."""

    def render_response(self, results: list[dict]) -> HttpResponse:
        """Render health check results into an HTTP text response.

        Args:
            results: The health check results to render.

        Returns:
            An HTTP response with health check results in Prometheus format.
        """

        lines = [
            "# HELP keystone_health_check_status Health check status (200 = healthy, 500 = unhealthy)",
            "# TYPE keystone_health_check_status gauge",
        ]

        for row in results:
            metric_value = 200 if row["healthy"] else 500
            lines.append(f'keystone_health_check_status{{check="{row["check"]}"}} {metric_value:.1f}')

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
