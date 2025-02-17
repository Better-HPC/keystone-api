"""Unit tests for the `AllocationRequestStatusChoicesView` class."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.allocations.models import AllocationRequest
from apps.allocations.views import AllocationRequestStatusChoicesView


class GetMethod(TestCase):
    """Test fetching choice values via the `get` method."""

    def test_roles_match_request_model(self) -> None:
        """Verify the response body contains the same membership roles used by the `AllocationRequest` model."""

        request = APIRequestFactory().get('/')
        response = AllocationRequestStatusChoicesView().get(request)

        expected_roles = dict(AllocationRequest.StatusChoices.choices)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_roles, response.data)
