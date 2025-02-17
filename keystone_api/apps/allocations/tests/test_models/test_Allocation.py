"""Unit tests for the `Allocation` class."""

from django.test import TestCase

from apps.allocations.models import Allocation, AllocationRequest, Cluster
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of an allocation's parent team via the `get_team` method.."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')
        self.cluster = Cluster.objects.create(name='Test Cluster')
        self.allocation_request = AllocationRequest.objects.create(team=self.team)
        self.allocation = Allocation.objects.create(
            requested=100,
            cluster=self.cluster,
            request=self.allocation_request
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        team = self.allocation.get_team()
        self.assertEqual(team, self.team)
