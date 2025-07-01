"""Function tests for the `/research/publications/<pk>/` endpoint."""

from datetime import date

from rest_framework.test import APITestCase

from apps.research_products.models import Publication
from .common import RecordEndpointPermissionsTests


class EndpointPermissions(RecordEndpointPermissionsTests, APITestCase):
    """Test endpoint user permissions."""

    model = Publication
    endpoint_pattern = '/research/publications/{pk}/'

    def build_valid_record_data(self) -> dict:
        """Return a dictionary with valid Publication data."""

        return {
            'title': 'foo',
            'abstract': 'bar',
            'journal': 'baz',
            'date': date(1990, 1, 1),
            'team': self.team.id
        }
