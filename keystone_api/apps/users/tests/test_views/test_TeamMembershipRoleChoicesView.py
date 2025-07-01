"""Unit tests for the `MembershipRoleChoicesView` class."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.users.models import Membership
from apps.users.views import MembershipRoleChoicesView


class GetMethod(TestCase):
    """Test fetching choice values via the `get` method."""

    def test_roles_match_membership_model(self) -> None:
        """Verify the response body contains the same membership roles used by the `Membership` model."""

        request = APIRequestFactory().get('/')
        response = MembershipRoleChoicesView().get(request)

        expected_roles = dict(Membership.Role.choices)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_roles, response.data)
