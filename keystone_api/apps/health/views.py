"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

import re
from abc import ABC, abstractmethod

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiExample
from health_check.mixins import CheckMixin
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['HealthCheckView', 'HealthCheckJsonView', 'HealthCheckPrometheusView']


class BaseHealthCheckView(GenericAPIView, CheckMixin, ABC):
    """Abstract base view for rendering health checks.

    Subclasses must implement the `render_response` method to define the
    desired format of rendered health check results.
    """

    @property
    @abstractmethod
    def cache_key(self) -> str:
        """Cache key used to store and retrieve the view's health check response."""

    @staticmethod
    @abstractmethod
    def render_response(plugins: dict) -> HttpResponse:
        """Render the response based on the view's specific format."""

    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Check system health and return the appropriate response."""

        cached_response = cache.get(self.cache_key)
        if cached_response:
            return cached_response

        self.check()
        response = self.render_response(self.plugins)

        # Cache the full HttpResponse object for 60 seconds
        cache.set(self.cache_key, response, 60)
        return response


@extend_schema_view(
    get=extend_schema(
        auth=[],
        summary="Retrieve the current application health status",
        description="Return a 200 status if all application health checks pass and a 500 status otherwise.",
        tags=["Application Health"],
        responses={
            '200': inline_serializer('health_ok', fields=dict()),
            '500': inline_serializer('health_error', fields=dict()),
        }
    )
)
class HealthCheckView(BaseHealthCheckView):
    """Return a 200 status code if all health checks pass and 500 otherwise."""

    permission_classes = []
    cache_key = 'healthcheck_cache'

    @staticmethod
    def render_response(plugins: dict) -> HttpResponse:
        """Return an HTTP response with a status code matching system health checks.

        Args:
            plugins: A mapping of healthcheck names to health check objects.

        Returns:
            An HttpResponse with status 200 if all checks are passing or 500 otherwise.
        """

        for plugin in plugins.values():
            if plugin.status != 1:
                return HttpResponse(status=500)

        return HttpResponse()


@extend_schema_view(
    get=extend_schema(
        auth=[],
        summary="Retrieve application health checks in JSON format",
        description=(
            "Retrieve results from individual application health checks in JSON format. "
            "This endpoint returns a `200` status code regardless of whether individual health checks are passing."
        ),
        tags=["Application Health"],
        responses={
            '200': inline_serializer('health_json_ok', fields={
                'healthCheckName': inline_serializer(
                    name='NestedInlineOneOffSerializer',
                    fields={
                        'status': serializers.IntegerField(default=200),
                        'message': serializers.CharField(default='working'),
                        'critical_service': serializers.BooleanField(default=True),
                    })
            })
        },
        examples=[
            OpenApiExample(
                name='Passing JSON Health Check',
                value={
                    "DatabaseBackend": {
                        "status": 200,
                        "message": "working",
                        "critical_service": True
                    }
                }
            ),
            OpenApiExample(
                name='Failing JSON Health Check',
                value={
                    "DatabaseBackend": {
                        "status": 500,
                        "message": "database unreachable",
                        "critical_service": True
                    }
                },
            )
        ]
    )
)
class HealthCheckJsonView(BaseHealthCheckView):
    """API endpoints for fetching application health checks in JSON format."""

    permission_classes = []
    cache_key = 'healthcheck_json_cache'

    @staticmethod
    def render_response(plugins: dict) -> JsonResponse:
        """Return a JSON response summarizing a collection of health checks.

        Args:
            plugins: A mapping of healthcheck names to health check objects.

        Returns:
            A JSON response.
        """

        data = dict()
        for plugin_name, plugin in plugins.items():
            data[plugin_name] = {
                'status': 200 if plugin.status == 1 else 500,
                'message': plugin.pretty_status(),
                'critical_service': plugin.critical_service
            }

        return JsonResponse(data=data)


@extend_schema_view(
    get=extend_schema(
        auth=[],
        summary="Retrieve application health checks in Prometheus format",
        description=(
            "Retrieve results from individual application health checks in Prometheus format. "
            "This endpoint returns a `200` status code regardless of whether individual health checks are passing."
        ),
        tags=["Application Health"],
        responses={
            (200, 'text/plain'): OpenApiTypes.STR
        },
        examples=[
            OpenApiExample(
                name="Passing Prometheus Health Check",
                media_type="text/plain",
                value=(
                    "# HELP DatabaseBackend health_check.db.backendsDatabaseBackend\n"
                    "# TYPE DatabaseBackend gauge\n"
                    "DatabaseBackend{critical_service=\"True\",message=\"working\"} 200.0"
                )
            ),
            OpenApiExample(
                name="Failing Prometheus Health Check",
                media_type="text/plain",
                value=(
                    "# HELP DatabaseBackend health_check.db.backendsDatabaseBackend\n"
                    "# TYPE DatabaseBackend gauge\n"
                    "DatabaseBackend{critical_service=\"True\",message=\"database unreachable\"} 500.0"
                )
            )
        ]
    )
)
class HealthCheckPrometheusView(BaseHealthCheckView):
    """API endpoints for fetching application health checks in Prometheus format."""

    permission_classes = []
    cache_key = 'healthcheck_prom_cache'

    @staticmethod
    def sanitize_metric_name(name: str) -> str:
        """Sanitize a Prometheus metric name.

        Replaces invalid characters found in health check names with underscores.

        Args:
            name: The metric name to sanitize.

        Returns:
            The sanitized metric name.
        """

        # Replace invalid characters with '_'
        name = re.sub(r'[^a-zA-Z0-9_:]', '_', name)

        # Ensure the first character is valid (letter, '_' or ':')
        if not re.match(r'^[a-zA-Z_:]', name):
            name = '_' + name

        return name

    def render_response(self, plugins: dict) -> HttpResponse:
        """Return an HTTP response summarizing a collection of health checks.

        Args:
            plugins: A mapping of healthcheck names to health check objects.

        Returns:
            An HTTP response.
        """

        prom_format = (
            '# HELP {name} {module}\n'
            '# TYPE {name} gauge\n'
            '{name}{{critical_service="{critical_service}",message="{message}"}} {status:.1f}'
        )

        status_data = []
        for plugin_name, plugin in plugins.items():
            status_data.append(
                prom_format.format(
                    name=self.sanitize_metric_name(plugin_name),
                    critical_service=plugin.critical_service,
                    message=plugin.pretty_status(),
                    status=200 if plugin.status else 500,
                    module=plugin.__class__.__module__ + plugin.__class__.__name__
                )
            )

        return HttpResponse('\n\n'.join(status_data), content_type="text/plain")
