"""Function tests for the `logging:task-detail` endpoint."""

from rest_framework.test import APITestCase

from apps.logging.factories import TaskResultFactory
from .common import LogDetailEndpointPermissionTestMixin

VIEW_NAME = "logging:task-detail"


class EndpointPermissions(LogDetailEndpointPermissionTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the parent mixin class for details on the tested endpoint permissions.
    """

    view_name = VIEW_NAME
    factory = TaskResultFactory
