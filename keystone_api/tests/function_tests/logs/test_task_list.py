"""Function tests for the `logging:task-list` endpoint."""

from django.urls import reverse
from rest_framework.test import APITestCase

from .common import LogListEndpointPermissionTestMixin

VIEW_NAME = "logging:task-list"


class EndpointPermissions(LogListEndpointPermissionTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the parent mixin class for details on the tested endpoint permissions.
    """

    endpoint = reverse(VIEW_NAME)
