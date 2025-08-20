"""Unit tests for the `AllocationReviewSerializer` class."""

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError

from apps.allocations.factories import AllocationRequestFactory
from apps.allocations.models import AllocationReview
from apps.allocations.serializers import AllocationReviewSerializer
from apps.users.factories import TeamFactory, UserFactory
from apps.users.models import User


class ValidateReviewerMethod(TestCase):
    """Test validation of the `reviewer` field."""

    def setUp(self) -> None:
        """Create dummy user accounts and test data."""

        self.user = UserFactory()
        self.different_user = UserFactory()

        self.team = TeamFactory()
        self.request = AllocationRequestFactory(team=self.team)

    @staticmethod
    def _create_serializer_with_post(requesting_user: User, data: dict) -> AllocationReviewSerializer:
        """Return a serializer instance for handling a POST request from the given user.

        Args:
            requesting_user: The authenticated user tied to the serialized HTTP request.
            data: The request data to be serialized.
        """

        request = RequestFactory().post('/reviews/')
        request.user = requesting_user
        request.data = data

        return AllocationReviewSerializer(data=data, context={'request': request})

    def test_reviewer_matches_submitter(self) -> None:
        """Verify validation passes when the reviewer is the user submitting the HTTP request."""

        # Create a POST where the submitter matches the reviewer
        post_data = {
            'request': self.request.id,
            'reviewer': self.user.id,
            'status': AllocationReview.StatusChoices.APPROVED
        }

        serializer = self._create_serializer_with_post(self.user, post_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_different_reviewer_from_submitter(self) -> None:
        """Verify validation fails when the reviewer is different from the user submitting the HTTP request."""

        # Create a POST where the submitter is different from the reviewer
        post_data = {
            'request': self.request.id,
            'reviewer': self.user.id,
            'status': AllocationReview.StatusChoices.APPROVED
        }

        serializer = self._create_serializer_with_post(self.different_user, post_data)
        with self.assertRaisesRegex(ValidationError, "Reviewer cannot be set to a different user"):
            serializer.is_valid(raise_exception=True)

    def test_reviewer_is_optional(self) -> None:
        """Verify the reviewer field is optional."""

        post_data = {
            'request': self.request.id,
            'status': AllocationReview.StatusChoices.APPROVED
        }

        serializer = self._create_serializer_with_post(self.user, post_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
