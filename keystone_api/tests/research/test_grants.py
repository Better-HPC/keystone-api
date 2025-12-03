"""Function tests for the `/research/grants/` endpoint."""

from datetime import date

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.research_products.factories import GrantFactory
from tests.utils import TeamListFilteringTestMixin
from .common import ResearchListEndpointPermissionsTestMixin

VIEW_NAME = "research:grant-list"


class EndpointPermissions(ResearchListEndpointPermissionsTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the `ResearchListEndpointPermissionsTests` class docstring for details on the
    tested endpoint permissions.
    """

    endpoint = reverse(VIEW_NAME)

    def build_valid_record_data(self) -> dict:
        """Return a dictionary containing valid Grant data."""

        return {
            'title': f"Grant ({self.team.name})",
            'agency': "Agency Name",
            'amount': 1000,
            'start_date': date(2000, 1, 1),
            'end_date': date(2000, 1, 31),
            'grant_number': 'abc-123',
            'team': self.team.pk
        }


class TeamRecordFiltering(TeamListFilteringTestMixin, APITestCase):
    """Test the filtering of returned records based on user team membership."""

    endpoint = reverse(VIEW_NAME)
    factory = GrantFactory
