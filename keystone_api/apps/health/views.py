"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from abc import ABC, abstractmethod

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, inline_serializer
from health_check.mixins import CheckMixin
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

__all__ = ['HealthCheckView', 'HealthCheckJsonView', 'HealthCheckPrometheusView']


class BaseHealthCheckView(GenericAPIView, CheckMixin, ABC):
    """Abstract base view for rendering health checks."""

    @staticmethod
    @abstractmethod
    def render_response(plugins: dict) -> HttpResponse:
        """Render the response based on the view's specific format."""

    @method_decorator(cache_page(60))
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Check system health and return the appropriate response."""

        self.check()
        return self.render_response(self.plugins)


class HealthCheckView(BaseHealthCheckView):
    """Return a 200 status code if all health checks pass and 500 otherwise."""

    permission_classes = []

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

    @extend_schema(responses={
        '200': inline_serializer('health_ok', fields=dict()),
        '500': inline_serializer('health_error', fields=dict()),
    })
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Summarize health checks in Prometheus format."""

        return super().get(request, *args, **kwargs)  # pragma: nocover


class HealthCheckJsonView(BaseHealthCheckView):
    """Return system health checks in JSON format."""

    permission_classes = []

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

        return JsonResponse(data=data, status=200)

    @extend_schema(responses={
        '200': inline_serializer('health_json_ok', fields={
            'healthCheckName': inline_serializer(
                name='NestedInlineOneOffSerializer',
                fields={
                    'status': serializers.IntegerField(default=200),
                    'message': serializers.CharField(default='working'),
                    'critical_service': serializers.BooleanField(default=True),
                })
        })
    })
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Summarize health checks in JSON format."""

        return super().get(request, *args, **kwargs)  # pragma: nocover


class HealthCheckPrometheusView(BaseHealthCheckView):
    """Return system health checks in Prometheus format."""

    permission_classes = []

    @staticmethod
    def render_response(plugins: dict) -> HttpResponse:
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

        status_data = [
            prom_format.format(
                name=plugin_name,
                critical_service=plugin.critical_service,
                message=plugin.pretty_status(),
                status=200 if plugin.status else 500,
                module=plugin.__class__.__module__ + plugin.__class__.__name__
            ) for plugin_name, plugin in plugins.items()
        ]

        return HttpResponse('\n\n'.join(status_data), status=200, content_type="text/plain")

    @extend_schema(responses={
        '200': inline_serializer('health_prom_ok', fields=dict()),
    })
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Summarize health checks in Prometheus format."""

        return super().get(request, *args, **kwargs)  # pragma: nocover
