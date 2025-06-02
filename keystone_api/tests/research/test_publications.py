"""Function tests for the `/research/publications/` endpoint."""

import datetime

from rest_framework.test import APITestCase

from .common import ListEndpointPermissionsTests


class EndpointPermissions(ListEndpointPermissionsTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/research/publications/'

    def build_valid_record_data(self) -> dict:
        """Return a dictionary with valid Publication data."""

        return {
            'title': 'foo',
            'abstract': 'bar',
            'journal': 'baz',
            'date': datetime.date(1990, 1, 1),
            'team': self.team.pk
        }
