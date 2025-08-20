"""Unit tests for the `JobStats` class."""

from django.test import TestCase

from apps.allocations.factories import JobStatsFactory
from apps.allocations.models import JobStats
from apps.users.factories import TeamFactory
from apps.users.models import Team


class GetTeamMethod(TestCase):
    """Test the retrieval of a comment's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock database records"""

        self.team = TeamFactory(name='Test Team')
        self.jobstat = JobStatsFactory(team=self.team)

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.jobstat.get_team())
