"""Function tests for the `research:publication-detail` endpoint."""

from datetime import date

from rest_framework.test import APITestCase

from apps.research_products.factories import PublicationFactory
from .common import ResearchDetailEndpointPermissionsTestMixin

VIEW_NAME = "research:publication-detail"


class EndpointPermissions(ResearchDetailEndpointPermissionsTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the parent mixin class for details on the tested endpoint permissions.
    """

    view_name = VIEW_NAME
    factory = PublicationFactory

    def build_valid_record_data(self) -> dict:
        """Return a dictionary containing valid Publication data."""

        return {
            'title': 'foo',
            'abstract': 'bar',
            'journal': 'baz',
            'date': date(1990, 1, 1),
            'team': self.team.id
        }
