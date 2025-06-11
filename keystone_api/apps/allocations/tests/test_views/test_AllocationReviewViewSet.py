"""Unit tests for the `AllocationReviewViewSet` class."""

from django.test import RequestFactory, TestCase
from rest_framework import status

from apps.allocations.models import AllocationRequest, AllocationReview
from apps.allocations.views import AllocationReviewViewSet
from apps.users.models import User


class CreateMethod(TestCase):
    """Test the creation of new records via the `create` method."""

    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load test data from fixtures."""

        self.staff_user = User.objects.get(username='staff_user')
        self.allocation_request = AllocationRequest.objects.get(pk=1)

    @staticmethod
    def _create_viewset_with_post(requesting_user: User, data: dict) -> AllocationReviewViewSet:
        """Create a new viewset instance with a mock POST request.

        Args:
            requesting_user: The authenticated user tied to the serialized HTTP request.
            data: The HTTP request data.
        """

        request = RequestFactory().post('/dummy-endpoint/')
        request.data = data
        request.user = requesting_user

        viewset = AllocationReviewViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        return viewset

    def test_reviewer_field_is_missing(self) -> None:
        """Verify the reviewer field is automatically set to the current user."""

        data = {'request': self.allocation_request.id, 'status': 'AP'}
        viewset = self._create_viewset_with_post(self.staff_user, data)
        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.staff_user.id)

        review = AllocationReview.objects.get(pk=response.data['id'])
        self.assertEqual(review.reviewer, self.staff_user)
        self.assertEqual(review.request, self.allocation_request)
        self.assertEqual(review.status, 'AP')

    def test_reviewer_field_is_provided(self) -> None:
        """Verify the reviewer field in the request data is respected if provided."""

        data = {'request': self.allocation_request.id, 'reviewer': self.staff_user.id, 'status': 'AP'}
        viewset = self._create_viewset_with_post(self.staff_user, data)
        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.staff_user.id)

        review = AllocationReview.objects.get(pk=response.data['id'])
        self.assertEqual(review.reviewer, self.staff_user)
        self.assertEqual(review.request, self.allocation_request)
        self.assertEqual(review.status, 'AP')
