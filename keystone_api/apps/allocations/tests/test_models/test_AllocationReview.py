"""Unit tests for the `AllocationReview` class."""

from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory, AllocationReviewFactory
from apps.allocations.models import AllocationRequest, AllocationReview
from apps.users.factories import TeamFactory, UserFactory
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of a review's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        # Create a Team instance
        self.user = UserFactory(username='pi', password='foobar123!')
        self.team = TeamFactory(name='Test Team')

        # Create an AllocationRequest instance linked to the team
        self.allocation_request = AllocationRequestFactory(
            title='Test Request',
            description='A test description',
            team=self.team
        )

        # Create an AllocationReview instance linked to the AllocationRequest
        self.reviewer = UserFactory(username='reviewer', password='foobar123!')
        self.allocation_review = AllocationReviewFactory(
            status=AllocationReview.StatusChoices.APPROVED,
            request=self.allocation_request,
            reviewer=self.reviewer
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation_review.get_team())
