"""Function tests for the `/stats/publications/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.research_products.factories import PublicationFactory
from apps.users.factories import MembershipFactory, UserFactory
from apps.users.models import Membership
from tests.utils import CustomAsserts

ENDPOINT = '/stats/publications/'


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


class TeamRecordFiltering(APITestCase):
    """Test returned metrics are filtered by user team membership."""

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership_1 = MembershipFactory(role=Membership.Role.MEMBER)
        self.team_1 = membership_1.team
        self.team_1_user = membership_1.user
        self.team_1_records = [
            PublicationFactory(team=self.team_1) for _ in range(2)
        ]

        membership_2 = MembershipFactory(role=Membership.Role.MEMBER)
        self.user_2 = membership_2.user
        self.team_2 = membership_2.team
        self.team_2_records = [
            PublicationFactory(team=self.team_2) for _ in range(3)
        ]

        self.staff_user = UserFactory(is_staff=True)
        self.all_records = self.team_1_records + self.team_2_records

    def test_generic_user_statistics(self) -> None:
        """Verify general users are only returned statistics from teams they are a member of."""

        self.client.force_authenticate(self.team_1_user)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.team_1_records), stats["publications_count"])

    def test_staff_user_statistics(self) -> None:
        """Verify staff users are returned aggregated statistics across all teams."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.all_records), stats["publications_count"])
