"""Function tests for the `/logs/audit/` endpoint."""

from rest_framework.test import APITestCase

from .common import BaseEndpointPermissionTests


class EndpointPermissions(BaseEndpointPermissionTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/logs/audit/'
    fixtures = ['testing_common.yaml']
