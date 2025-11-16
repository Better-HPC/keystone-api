"""Function tests for the `/stats/grants/` endpoint."""
import datetime

from rest_framework import status
from rest_framework.test import APITestCase

from apps.research_products.factories import GrantFactory
from apps.users.factories import MembershipFactory, UserFactory
from apps.users.models import Membership
from tests.utils import CustomAsserts

ENDPOINT = '/stats/grants/'


class EndpointPermissions(CustomAsserts, APITestCase):
    """Test endpoint user permissions."""

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory()

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated have read only permissions."""

        self.client.force_login(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TeamGrantFiltering(APITestCase):
    """Test returned grant metrics are filtered by user team membership."""

    endpoint = ENDPOINT  # e.g. reverse("grant-stats-list")

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership_1 = MembershipFactory(role=Membership.Role.MEMBER)
        self.team_1 = membership_1.team
        self.team_1_user = membership_1.user
        self.team_1_records = [
            GrantFactory(team=self.team_1) for _ in range(3)
        ]

        membership_2 = MembershipFactory(role=Membership.Role.MEMBER)
        self.user_2 = membership_2.user
        self.team_2 = membership_2.team
        self.team_2_records = [
            GrantFactory(team=self.team_2) for _ in range(3)
        ]

        self.staff_user = UserFactory(is_staff=True)
        self.all_records = self.team_1_records + self.team_2_records

    def _assert_stats(self, stats: dict, records: list) -> None:
        """Assert returned statistics match the provided records.

        Args:
            stats: Statistics returned by the API.
            records: The records used to calculate the statistics.
        """

        today = datetime.date.today()

        # Funding totals
        expected_funding_total = sum(float(g.amount) for g in records)
        self.assertAlmostEqual(expected_funding_total, float(stats["funding_total"]), places=2)

        # Funding average
        expected_avg = expected_funding_total / len(records)
        self.assertAlmostEqual(expected_avg, float(stats["funding_average"]), places=2)

        # Grant count
        self.assertEqual(len(records), stats["grant_count"])

        # Active / expired counts
        expected_active = sum(1 for g in records if g.end_date >= today)
        self.assertEqual(expected_active, stats["active_count"])

        expected_expired = sum(1 for g in records if g.end_date < today)
        self.assertEqual(expected_expired, stats["expired_count"])

        # Agencies count
        self.assertEqual(len({g.agency for g in records}), stats["agency_count"])

    def test_generic_user_statistics(self) -> None:
        """Verify general users only receive statistics for their teams."""

        self.client.force_authenticate(self.team_1_user)
        response = self.client.get(self.endpoint)
        self._assert_stats(response.json(), self.team_1_records)

    def test_staff_user_statistics(self) -> None:
        """Verify staff users receive statistics aggregated across all teams."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint)
        self._assert_stats(response.json(), self.all_records)
