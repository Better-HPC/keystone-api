"""Unit tests for the `GrantViewSet` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.research_products.models import Grant
from apps.research_products.views import GrantViewSet
from apps.users.models import Team

User = get_user_model()


class GetQuerysetMethod(TestCase):
    """Test record filtering in the DB query returned by the `get_queryset` method."""

    def setUp(self) -> None:
        """Create user accounts and research grants."""

        self.staff_user = User.objects.create(username='staff', is_staff=True)
        self.general_user = User.objects.create(username='general')

        self.team1 = Team.objects.create(name='Team1')
        self.team1_user = User.objects.create(username='user1')
        self.team1.add_or_update_member(self.team1_user)

        self.team1_grant = Grant.objects.create(
            title="Grant 1",
            agency="Agency 1",
            amount=100000.00,
            grant_number="G-123",
            fiscal_year=2020,
            start_date="2020-01-01",
            end_date="2021-01-01",
            team=self.team1
        )

        self.team2_user = User.objects.create(username='user2')
        self.team2 = Team.objects.create(name='Team2')
        self.team2.add_or_update_member(self.team2_user)

        self.team2_grant = Grant.objects.create(
            title="Grant 2",
            agency="Agency 2",
            amount=200000.00,
            grant_number="G-456",
            fiscal_year=2021,
            start_date="2021-01-01",
            end_date="2022-01-01",
            team=self.team2
        )

    def create_viewset(self, user: User) -> GrantViewSet:
        """Create a viewset for testing purposes.

        Args:
            user: The user submitting a request to the viewset.

        Returns:
            A viewset instance tied to a request from the given user.
        """

        viewset = GrantViewSet()
        viewset.request = self.client.request().wsgi_request
        viewset.request.user = user
        return viewset

    def test_queryset_for_staff_user(self) -> None:
        """Verify staff users are returned a query including all grants."""

        viewset = self.create_viewset(self.staff_user)
        queryset = viewset.get_queryset()
        self.assertEqual(len(queryset), 2)

    def test_queryset_for_team_member(self) -> None:
        """Verify team members are returned a query including only their team's grants."""

        viewset = self.create_viewset(self.team1_user)
        queryset = viewset.get_queryset()
        self.assertEqual(len(queryset), 1)
        self.assertEqual(queryset[0].team, self.team1)

    def test_queryset_for_non_team_member(self) -> None:
        """Verify non-members are returned a query including no grants."""

        viewset = self.create_viewset(self.general_user)
        queryset = viewset.get_queryset()
        self.assertEqual(len(queryset), 0)
