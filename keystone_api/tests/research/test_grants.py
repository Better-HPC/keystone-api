"""Function tests for the `/research/grants/` endpoint."""

from datetime import date

from rest_framework.test import APITestCase

from apps.research_products.models import Grant
from tests.utils import TeamScopedListFilteringTests
from .common import ListEndpointPermissionsTests


class EndpointPermissions(ListEndpointPermissionsTests, APITestCase):
    """Test endpoint user permissions."""

    endpoint = '/research/grants/'

    def build_valid_record_data(self) -> dict:
        """Return a dictionary with valid Grant data."""

        return {
            'title': f"Grant ({self.team.name})",
            'agency': "Agency Name",
            'amount': 1000,
            'fiscal_year': 2001,
            'start_date': date(2000, 1, 1),
            'end_date': date(2000, 1, 31),
            'grant_number': 'abc-123',
            'team': self.team.pk
        }


class RecordFiltering(TeamScopedListFilteringTests, APITestCase):
    """Test the filtering of returned records based on user team membership."""

    endpoint = '/research/grants/'
    model = Grant
