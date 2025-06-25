"""Unit tests for the `Comment` class."""

from django.test import TestCase

from apps.allocations.models import AllocationRequest, Comment
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of a comment's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock database records"""

        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')
        self.allocation_request = AllocationRequest.objects.create(
            title='Test Request',
            description='A test description',
            team=self.team
        )

        self.comment = Comment.objects.create(
            user=self.user,
            content='This is a test.',
            request=self.allocation_request,
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.comment.get_team())
