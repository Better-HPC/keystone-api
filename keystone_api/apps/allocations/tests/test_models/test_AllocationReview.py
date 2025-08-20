"""Unit tests for the `AllocationReview` class."""

from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory, AllocationReviewFactory
from apps.allocations.models import AllocationReview
from apps.users.factories import TeamFactory


class GetTeamMethod(TestCase):
    """Test the retrieval of a review's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.team = TeamFactory()
        self.allocation_request = AllocationRequestFactory(team=self.team)

        # Create a review linked to a request submitted by `self.team`
        self.allocation_review = AllocationReviewFactory(
            status=AllocationReview.StatusChoices.APPROVED,
            request=self.allocation_request,
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.allocation_review.get_team())
