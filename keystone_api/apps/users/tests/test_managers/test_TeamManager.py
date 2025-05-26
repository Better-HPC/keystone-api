"""Unit tests for the `TeamManager` class."""

from django.test import TestCase

from apps.users.models import Membership, Team, User


class TeamsForUserMethod(TestCase):
    """Test fetching team affiliations via the `teams_for_user` method."""

    def setUp(self) -> None:
        """Create temporary users and teams."""

        self.test_user = User.objects.create(username='test_user')

        # Team where the test user is an owner
        self.team1 = Team.objects.create(name='Team1')
        self.team1.add_or_update_member(self.test_user, role=Membership.Role.OWNER)

        # Team where the test user is an admin
        self.team2 = Team.objects.create(name='Team2')
        self.team2.add_or_update_member(self.test_user, role=Membership.Role.ADMIN)

        # Team where the test user is an unprivileged member
        self.team3 = Team.objects.create(name='Team3')
        self.team3.add_or_update_member(self.test_user, role=Membership.Role.MEMBER)

        # Team where the test user has no role
        self.team4 = Team.objects.create(name='Team4')

    def test_teams_for_user(self) -> None:
        """Verify all teams are returned for a test user."""

        result = Team.objects.teams_for_user(self.test_user).all()
        self.assertCountEqual(result, [self.team1, self.team2, self.team3])
