"""Function tests for the `/logs/apps/` endpoint."""

from rest_framework.test import APITestCase

from .common import BaseEndpointPermissionTests


class EndpointPermissions(BaseEndpointPermissionTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/logs/apps/'
    fixtures = ['testing_common.yaml']
