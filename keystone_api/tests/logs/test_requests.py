"""Function tests for the `/logs/requests/` endpoint."""

from rest_framework.test import APITestCase

from .common import BaseEndpointPermissionTests


class EndpointPermissions(BaseEndpointPermissionTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/logs/requests/'
    fixtures = ['testing_common.yaml']
