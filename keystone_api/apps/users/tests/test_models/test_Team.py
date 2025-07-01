"""Unit tests for the `Team` model."""

from django.test import TestCase

from apps.users.models import Membership, Team, User


class GetMembers(TestCase):
    """Test fetching all team members via getter methods."""

    def setUp(self) -> None:
        """Create temporary user accounts for use in tests."""

        self.owner = User.objects.create(username='owner')
        self.admin = User.objects.create(username='admin')
        self.member1 = User.objects.create(username='unprivileged1')
        self.member2 = User.objects.create(username='unprivileged2')

        self.team = Team.objects.create(name="Test Team")
        self.team.add_or_update_member(self.owner, role=Membership.Role.OWNER)
        self.team.add_or_update_member(self.admin, role=Membership.Role.ADMIN)
        self.team.add_or_update_member(self.member1, role=Membership.Role.MEMBER)
        self.team.add_or_update_member(self.member2, role=Membership.Role.MEMBER)

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


class AddOrUpdateMemberMethod(TestCase):
    """Test the modification of team membership via the `add_or_update_member` method."""

    def setUp(self) -> None:
        """Set up test users and teams."""

        self.test_user1 = User.objects.create(username='user1')
        self.test_user2 = User.objects.create(username='user2')
        self.team = Team.objects.create(name='Test Team')

    def test_default_permissions(self) -> None:
        """Verify new members default to the `MEMBER` role."""

        membership = self.team.add_or_update_member(self.test_user1)
        self.assertEqual(membership.user, self.test_user1)
        self.assertEqual(membership.team, self.team)
        self.assertEqual(membership.role, Membership.Role.MEMBER)

        # Verify the membership record was created
        self.assertTrue(Membership.objects.filter(pk=membership.id).exists())

    def test_assigned_permissions(self) -> None:
        """Verify new members can be created with elevated permissions."""

        membership = self.team.add_or_update_member(self.test_user1, role=Membership.Role.OWNER)
        self.assertEqual(membership.user, self.test_user1)
        self.assertEqual(membership.team, self.team)
        self.assertEqual(membership.role, Membership.Role.OWNER)

        # Verify the membership record was created
        self.assertTrue(Membership.objects.filter(pk=membership.id).exists())

    def test_update_existing_member_role(self) -> None:
        """Verify new roles are saved for existing team members."""

        # Add user1 as a 'Member' then update to an 'Admin'
        self.team.add_or_update_member(self.test_user1, role=Membership.Role.MEMBER)
        membership = self.team.add_or_update_member(self.test_user1, role=Membership.Role.ADMIN)

        # Ensure the user's role is updated
        self.assertEqual(membership.role, Membership.Role.ADMIN)
        self.assertEqual(Membership.objects.filter(user=self.test_user1, team=self.team).count(), 1)

    def test_add_member_to_different_team(self) -> None:
        """Verify member addition is idempotent."""

        # Create a second team
        team2 = Team.objects.create(name='Second Team')

        # Add user1 to both teams with different roles
        membership1 = self.team.add_or_update_member(self.test_user1, role=Membership.Role.MEMBER)
        membership2 = team2.add_or_update_member(self.test_user1, role=Membership.Role.ADMIN)

        # Ensure the membership records are distinct
        self.assertNotEqual(membership1, membership2)
        self.assertEqual(membership1.role, Membership.Role.MEMBER)
        self.assertEqual(membership2.role, Membership.Role.ADMIN)

        # Check the user has membership in both teams
        self.assertTrue(Membership.objects.filter(user=self.test_user1, team=self.team).exists())
        self.assertTrue(Membership.objects.filter(user=self.test_user1, team=team2).exists())
