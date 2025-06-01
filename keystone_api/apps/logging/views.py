"""Application logic for rendering HTML templates and handling HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import permissions, viewsets

from .models import *
from .permissions import *
from .serializers import *

__all__ = [
    'AppLogViewSet',
    'AuditLogViewSet',
    'RequestLogViewSet',
    'TaskResultViewSet',
]


class AppLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns application log data."""

    queryset = AppLog.objects.all()
    serializer_class = AppLogSerializer
    search_fields = ['name', 'level', 'pathname', 'message', 'func', 'sinfo']
    permission_classes = [permissions.IsAuthenticated, IsAdminRead]


class RequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns HTTP request log data."""

    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    search_fields = ['endpoint', 'method', 'response_code', 'body_request', 'body_response', 'remote_address']
    permission_classes = [permissions.IsAuthenticated, IsAdminRead]


class TaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns results from scheduled background tasks."""

    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    search_fields = ['periodic_task_name', 'task_name', 'status', 'worker', 'result', 'traceback']
    permission_classes = [permissions.IsAuthenticated, IsAdminRead]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns results from the application audit log."""

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    search_fields = ['resource', 'action', 'user_username']
    permission_classes = [permissions.IsAuthenticated, IsAdminRead]
