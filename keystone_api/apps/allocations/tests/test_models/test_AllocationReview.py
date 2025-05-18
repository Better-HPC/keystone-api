"""Unit tests for the `AllocationReview` class."""

from django.test import TestCase

from apps.allocations.models import AllocationRequest, AllocationReview
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of a review's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        # Create a Team instance
        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')

        # Create an AllocationRequest instance linked to the team
        self.allocation_request = AllocationRequest.objects.create(
            title='Test Request',
            description='A test description',
            team=self.team
        )

        # Create an AllocationReview instance linked to the AllocationRequest
        self.reviewer = User.objects.create_user(username='reviewer', password='foobar123!')
        self.allocation_request_review = AllocationReview.objects.create(
            status=AllocationReview.StatusChoices.APPROVED,
            request=self.allocation_request,
            reviewer=self.reviewer
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        team = self.allocation_request_review.get_team()
        self.assertEqual(team, self.team)
