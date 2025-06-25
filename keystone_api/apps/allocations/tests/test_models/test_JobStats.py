"""Unit tests for the `JobStats` class."""

from django.test import TestCase

from apps.allocations.models import JobStats
from apps.users.models import Team


class GetTeamMethod(TestCase):
    """Test the retrieval of a comment's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock database records"""

        self.team = Team.objects.create(name='Test Team')
        self.jobstat = JobStats.objects.create(team=self.team)

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.jobstat.get_team())
