"""Application logic for rendering HTML templates and handling HTTP requests.

View objects handle the processing of incoming HTTP requests and return the
appropriately rendered HTML template or other HTTP response.
"""

from rest_framework import permissions, viewsets

from .models import *
from .serializers import *

__all__ = ['AppLogViewSet', 'RequestLogViewSet', 'TaskResultViewSet']


class AppLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns application log data."""

    queryset = AppLog.objects.all()
    serializer_class = AppLogSerializer
    search_fields = ['name', 'level', 'pathname', 'message', 'func', 'sinfo']
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class RequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns HTTP request log data."""

    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    search_fields = ['endpoint', 'method', 'response_code', 'body_request', 'body_response', 'remote_address']
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class TaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Returns results from scheduled background tasks."""

    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    search_fields = ['periodic_task_name', 'task_name', 'status', 'worker', 'result', 'traceback']
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
