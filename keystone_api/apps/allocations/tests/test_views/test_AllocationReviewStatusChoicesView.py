"""Unit tests for the `AllocationReviewStatusChoicesView` class."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.allocations.models import AllocationReview
from apps.allocations.views import AllocationReviewStatusChoicesView


class GetMethod(TestCase):
    """Test fetching choice values via the `get` method."""

    def test_roles_match_review_model(self) -> None:
        """Verify the response body contains the same membership roles used by the `AllocationReview` model."""

        request = APIRequestFactory().get('/')
        response = AllocationReviewStatusChoicesView().get(request)

        expected_roles = dict(AllocationReview.StatusChoices.choices)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_roles, response.data)
