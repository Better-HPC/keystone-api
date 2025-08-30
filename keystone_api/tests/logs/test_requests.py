"""Function tests for the `/logs/requests/` endpoint."""

from rest_framework.test import APITestCase

from .common import LogEndpointPermissionTestMixin


class EndpointPermissions(LogEndpointPermissionTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the `LogEndpointPermissionTests` class docstring for details on the
    tested endpoint permissions.
    """

    endpoint = '/logs/requests/'
