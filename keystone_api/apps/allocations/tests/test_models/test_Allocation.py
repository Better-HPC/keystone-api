"""Unit tests for the `Allocation` class."""

from django.test import TestCase

from apps.allocations.factories import AllocationFactory, AllocationRequestFactory
from apps.users.factories import TeamFactory


class GetTeamMethod(TestCase):
    """Test the retrieval of an allocation's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.team = TeamFactory()
        self.allocation = AllocationFactory(
            request=AllocationRequestFactory(team=self.team)
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation.get_team())
