"""Function tests for the `/logs/tasks/` endpoint."""

from rest_framework.test import APITestCase

from .common import LoggingPermissionTests


class EndpointPermissions(LoggingPermissionTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/logs/tasks/'
    fixtures = ['testing_common.yaml']
