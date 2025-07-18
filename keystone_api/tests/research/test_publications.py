"""Function tests for the `/research/publications/` endpoint."""

import datetime

from rest_framework.test import APITestCase

from apps.research_products.factories import PublicationFactory
from tests.utils import TeamScopedListFilteringTests
from .common import ListEndpointPermissionsTests


class EndpointPermissions(ListEndpointPermissionsTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/research/publications/'

    def build_valid_record_data(self) -> dict:
        """Return a dictionary containing valid Publication data."""

        return {
            'title': 'foo',
            'abstract': 'bar',
            'journal': 'baz',
            'date': datetime.date(1990, 1, 1),
            'team': self.team.pk
        }


class RecordFiltering(TeamScopedListFilteringTests, APITestCase):
    """Test the filtering of returned records based on user team membership."""

    factory = PublicationFactory
    endpoint = '/research/publications/'
