"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'AuditLogViewSet',
    'RequestLogViewSet',
    'TaskResultViewSet',
]


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs.",
        description=(
            "Returns a list of audit logs. "
            "Audit logs track changes to database records and are used for compliance and security auditing. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a single audit log.",
        description=(
            "Returns a single audit log by its ID. "
            "Audit logs track changes to database records and are used for compliance and security auditing. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    )
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for fetching audit logs."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRead]
    search_fields = ['resource', 'action', 'user_username']
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related('actor', 'content_type')


@extend_schema_view(
    list=extend_schema(
        summary="List HTTP request logs.",
        description=(
            "Returns a list of HTTP request logs. "
            "Request logs track incoming API requests and their resulting HTTP responses. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a single HTTP request log.",
        description=(
            "Returns a single HTTP request log by its ID. "
            "Request logs track incoming API requests and their resulting HTTP responses. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    )
)
class RequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for fetching HTTP request logs."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRead]
    search_fields = ['endpoint', 'method', 'response_code', 'body_request', 'body_response', 'remote_address']
    serializer_class = RequestLogSerializer
    queryset = RequestLog.objects.select_related('user')


@extend_schema_view(
    list=extend_schema(
        summary="List background task results.",
        description=(
            "Returns a list of task logs. "
            "Task logs are collected from the Celery backend to track background task outcomes. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a single background task result.",
        description=(
            "Returns a single task log by its ID. "
            "Task logs are collected from the Celery backend to track background task outcomes. "
            "Access to log records is restricted to staff users."
        ),
        tags=["Admin - Logging"],
    )
)
class TaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for fetching background task results."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRead]
    search_fields = ['periodic_task_name', 'task_name', 'status', 'worker', 'result', 'traceback']
    serializer_class = TaskResultSerializer
    queryset = TaskResult.objects.all()
