"""Function tests for the `stats:grant-list` endpoint."""

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.research_products.factories import GrantFactory
from apps.users.factories import MembershipFactory, UserFactory
from apps.users.models import Membership
from .common import StatisticEndpointPermissionsTestMixin

VIEW_NAME = 'stats:grant-detail'


class EndpointPermissions(StatisticEndpointPermissionsTestMixin, APITestCase):
    """Test endpoint user permissions.

    See the parent mixin class for details on the tested endpoint permissions.
    """

    endpoint = reverse(VIEW_NAME)


class TeamGrantFiltering(APITestCase):
    """Test returned grant metrics are filtered by user team membership."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership_1 = MembershipFactory(role=Membership.Role.MEMBER)
        self.team_1 = membership_1.team
        self.team_1_user = membership_1.user
        self.team_1_records = [
            GrantFactory(team=self.team_1) for _ in range(2)
        ]

        membership_2 = MembershipFactory(role=Membership.Role.MEMBER)
        self.user_2 = membership_2.user
        self.team_2 = membership_2.team
        self.team_2_records = [
            GrantFactory(team=self.team_2) for _ in range(3)
        ]

        self.staff_user = UserFactory(is_staff=True)
        self.all_records = self.team_1_records + self.team_2_records

    def test_generic_user_statistics(self) -> None:
        """Verify general users only receive statistics for their teams."""

        self.client.force_authenticate(self.team_1_user)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.team_1_records), stats["grant_count"])

    def test_staff_user_statistics(self) -> None:
        """Verify staff users receive statistics aggregated across all teams."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.all_records), stats["grant_count"])

    def test_team_filtered_statistics(self) -> None:
        """Verify query values can be used to filter returned statistics by team."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint, query_params={"team": self.team_1.id})

        stats = response.json()
        self.assertEqual(len(self.team_1_records), stats["grant_count"])
