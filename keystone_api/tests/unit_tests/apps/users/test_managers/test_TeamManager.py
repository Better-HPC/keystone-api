"""Unit tests for the `TeamManager` class."""

from django.test import TestCase

from apps.users.factories import MembershipFactory, TeamFactory
from apps.users.models import Team, User


class TeamsForUserMethod(TestCase):
    """Test fetching team affiliations via the `teams_for_user` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.test_user = User.objects.create(username="test_user")

        # Teams where the test user holds a membership
        self.team1 = MembershipFactory(user=self.test_user).team
        self.team2 = MembershipFactory(user=self.test_user).team
        self.team3 = MembershipFactory(user=self.test_user).team

        # Team where the test user has no role
        self.team4 = Team.objects.create()

    def test_affiliated_teams_are_returned(self) -> None:
        """Verify only teams with the user as a member are returned."""

        result = Team.objects.teams_for_user(self.test_user).all()
        self.assertCountEqual(result, [self.team1, self.team2, self.team3])

    def test_user_with_no_memberships(self) -> None:
        """Verify an empty queryset is returned for a user with no team affiliations."""

        unaffiliated_user = User.objects.create(username="unaffiliated_user")
        result = Team.objects.teams_for_user(unaffiliated_user).all()
        self.assertQuerySetEqual(result, [])

    def test_other_users_teams_are_excluded(self) -> None:
        """Verify teams affiliated only with other users are not returned."""

        # Team affiliated with a different user
        other_user = User.objects.create(username="other_user")
        MembershipFactory(user=other_user)

        result = Team.objects.teams_for_user(self.test_user).all()
        self.assertCountEqual(result, [self.team1, self.team2, self.team3])

    def test_inactive_teams_included_by_default(self) -> None:
        """Verify inactive teams are returned by default."""

        inactive_team = TeamFactory(is_active=False)
        MembershipFactory(user=self.test_user, team=inactive_team)

        result = Team.objects.teams_for_user(self.test_user).all()
        self.assertIn(inactive_team, result)

    def test_inactive_teams_excluded_when_flag_disabled(self) -> None:
        """Verify inactive teams are not returned when `include_inactive` is `False`."""

        inactive_team = TeamFactory(is_active=False)
        MembershipFactory(user=self.test_user, team=inactive_team)

        result = Team.objects.teams_for_user(self.test_user, include_inactive=False).all()
        self.assertNotIn(inactive_team, result)
        # Active memberships from setUp should still be returned
        self.assertCountEqual(result, [self.team1, self.team2, self.team3])
