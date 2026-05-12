"""Unit tests for the `MembershipSerializer` class."""

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.users.factories import TeamFactory, UserFactory
from apps.users.models import Membership
from apps.users.serializers import MembershipSerializer


class ValidateMethod(TestCase):
    """Test record validation via the `validate` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.factory = APIRequestFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.generic_user = UserFactory()
        self.active_team = TeamFactory(is_active=True)
        self.inactive_team = TeamFactory(is_active=False)
        self.target_user = UserFactory()

    def test_non_staff_create_active_team(self) -> None:
        """Verify non-staff users can create memberships for active teams."""

        request = self.factory.post("/")
        request.user = self.generic_user

        serializer = MembershipSerializer(
            data={"team": self.active_team.pk, "user": self.target_user.pk, "role": Membership.Role.MEMBER},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_staff_create_inactive_team(self) -> None:
        """Verify non-staff users cannot create memberships for inactive teams."""

        request = self.factory.post("/")
        request.user = self.generic_user

        serializer = MembershipSerializer(
            data={"team": self.inactive_team.pk, "user": self.target_user.pk, "role": Membership.Role.MEMBER},
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("team", serializer.errors)

    def test_staff_create_active_team(self) -> None:
        """Verify staff users can create memberships for active teams."""

        request = self.factory.post("/")
        request.user = self.staff_user

        serializer = MembershipSerializer(
            data={"team": self.active_team.pk, "user": self.target_user.pk, "role": Membership.Role.MEMBER},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_staff_create_inactive_team(self) -> None:
        """Verify staff users can create memberships for inactive teams."""

        request = self.factory.post("/")
        request.user = self.staff_user

        serializer = MembershipSerializer(
            data={"team": self.inactive_team.pk, "user": self.target_user.pk, "role": Membership.Role.MEMBER},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
