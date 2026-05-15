"""Function tests for the `logging:request-detail` endpoint."""

from rest_framework.test import APITestCase

from apps.logging.factories import RequestLogFactory
from .common import LogDetailEndpointPermissionTestMixin

VIEW_NAME = "logging:request-detail"


class EndpointPermissions(LogDetailEndpointPermissionTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the parent mixin class for details on the tested endpoint permissions.
    """

    view_name = VIEW_NAME
    factory = RequestLogFactory
