"""Function tests for the `/research/grants/` endpoint."""

from datetime import date

from rest_framework.test import APITestCase

from apps.research_products.factories import GrantFactory
from tests.utils import TeamScopedListFilteringTestMixin
from .common import ResearchListEndpointPermissionsTestMixin


class EndpointPermissions(ResearchListEndpointPermissionsTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the `ResearchListEndpointPermissionsTests` class docstring for details on the
    tested endpoint permissions.
    """

    endpoint = '/research/grants/'

    def build_valid_record_data(self) -> dict:
        """Return a dictionary containing valid Grant data."""

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


class RecordFiltering(TeamScopedListFilteringTestMixin, APITestCase):
    """Test the filtering of returned records based on user team membership."""

    factory = GrantFactory
    endpoint = '/research/grants/'
