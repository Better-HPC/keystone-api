"""Unit tests for the `Allocation` class."""

from django.test import TestCase

from apps.allocations.factories import AllocationFactory, AllocationRequestFactory, ClusterFactory
from apps.allocations.models import Allocation, AllocationRequest, Cluster
from apps.users.factories import TeamFactory, UserFactory
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of an allocation's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.user = UserFactory(username='pi', password='foobar123!')
        self.team = TeamFactory(name='Test Team')
        self.cluster = ClusterFactory(name='Test Cluster')
        self.allocation_request = AllocationRequestFactory(team=self.team)
        self.allocation = AllocationFactory(
            requested=100,
            cluster=self.cluster,
            request=self.allocation_request
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation.get_team())
