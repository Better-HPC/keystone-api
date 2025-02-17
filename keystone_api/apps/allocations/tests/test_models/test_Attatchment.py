"""Unit tests for the `Attachment` class."""

from django.test import TestCase

from apps.allocations.models import AllocationRequest, Attachment
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of an attachment's parent team via the `get_team` method.."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')
        self.allocation_request = AllocationRequest.objects.create(
            title='Test Request',
            description='A test description',
            team=self.team
        )

        self.attachment = Attachment.objects.create(
            path='dummy.file',
            request=self.allocation_request,
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        team = self.attachment.get_team()
        self.assertEqual(team, self.team)
