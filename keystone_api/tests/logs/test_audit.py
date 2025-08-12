"""Function tests for the `/logs/audit/` endpoint."""

from rest_framework.test import APITestCase

from .common import LogEndpointPermissionTests


class EndpointPermissions(LogEndpointPermissionTests, APITestCase):
    """Test endpoint user permissions.

    See the `LogEndpointPermissionTests` class docstring for details on the
    tested endpoint permissions.
    """

    endpoint = '/logs/audit/'
