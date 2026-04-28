"""Unit tests for the `Team` model."""

from django.test import TestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership


class GetMemberMethods(TestCase):
    """Test fetching all team members via getter methods."""

    def setUp(self) -> None:
        """Create temporary user accounts for use in tests."""

        self.owner = UserFactory()
        self.admin = UserFactory()
        self.member1 = UserFactory()
        self.member2 = UserFactory()

        self.team = TeamFactory()
        MembershipFactory(user=self.owner, team=self.team, role=Membership.Role.OWNER)
        MembershipFactory(user=self.admin, team=self.team, role=Membership.Role.ADMIN)
        MembershipFactory(user=self.member1, team=self.team, role=Membership.Role.MEMBER)
        MembershipFactory(user=self.member2, team=self.team, role=Membership.Role.MEMBER)

    def test_get_all_members(self) -> None:
        """Verify the `get_all_members` method returns all team members."""

        expected_members = [self.owner, self.admin, self.member1, self.member2]
        self.assertQuerySetEqual(
            expected_members,
            self.team.get_all_members(),
            ordered=False
        )

    def test_get_privileged_members(self) -> None:
        """Verify the `get_privileged_members` method only returns privileged team members."""

        self.assertQuerySetEqual([self.owner, self.admin], self.team.get_privileged_members(), ordered=False)
