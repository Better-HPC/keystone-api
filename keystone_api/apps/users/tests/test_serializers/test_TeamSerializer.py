"""Unit tests for the `TeamSerializer` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.models import Team, TeamMembership
from apps.users.serializers import TeamSerializer

User = get_user_model()


class CreateMethod(TestCase):
    """Test case for the `create` method of `TeamSerializer`."""

    def setUp(self) -> None:
        """Define dummy team data."""

        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.team_data = {
            "name": "Test Team",
            "members": [
                {"user": self.user1, "role": TeamMembership.Role.ADMIN},
                {"user": self.user2, "role": TeamMembership.Role.MEMBER},
            ],
        }

        self.serializer = TeamSerializer(data=self.team_data)
        self.assertTrue(self.serializer.is_valid(), self.serializer.errors)

    def test_create_team_with_members(self) -> None:
        """Verify a team is created with the correct members."""

        team = self.serializer.create(self.serializer.validated_data)
        self.assertEqual("Test Team", team.name)
        self.assertEqual(2, team.members.count())
        self.assertEqual(TeamMembership.Role.ADMIN, team.members.get(user=self.user1).role)
        self.assertEqual(TeamMembership.Role.MEMBER, team.members.get(user=self.user2).role)

    def test_create_team_without_members(self) -> None:
        """Verify a team is created with the correct members."""

        team = self.serializer.create({"name": "Test Team"})
        self.assertEqual("Test Team", team.name)
        self.assertEqual(0, team.members.count())


class UpdateMethod(TestCase):
    """Test case for the `update` method of `TeamSerializer`."""

    def setUp(self) -> None:
        """Define dummy team and membership data."""

        self.team = Team.objects.create(name="Old Team Name")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")

        TeamMembership.objects.create(team=self.team, user=self.user1, role=TeamMembership.Role.OWNER)
        TeamMembership.objects.create(team=self.team, user=self.user2, role=TeamMembership.Role.MEMBER)

    def test_update_team(self) -> None:
        """Verify a team is updated correctly with new members and name."""

        update_data = {
            "name": "New Team Name",
            "members": [
                {"user": self.user1, "role": TeamMembership.Role.ADMIN},
                {"user": self.user3, "role": TeamMembership.Role.MEMBER},
            ],
        }

        serializer = TeamSerializer(instance=self.team)
        updated_team = serializer.update(self.team, update_data)

        # Make sure the team name and membership is updated
        self.assertEqual(updated_team.name, "New Team Name")
        self.assertEqual(TeamMembership.Role.ADMIN, updated_team.members.get(user=self.user1).role)
        self.assertEqual(TeamMembership.Role.MEMBER, updated_team.members.get(user=self.user3).role)

        # Old memberships are removed
        self.assertEqual(updated_team.members.count(), 2)
        self.assertFalse(updated_team.members.filter(user=self.user2).exists())

    def test_partial_update_team_name_only(self) -> None:
        """Verify a team can be partially updated by changing only the name."""

        update_data = {"name": "Partially Updated Team"}
        serializer = TeamSerializer(instance=self.team, partial=True)
        updated_team = serializer.update(self.team, update_data)

        self.assertEqual(updated_team.name, "Partially Updated Team")
        self.assertEqual(2, updated_team.members.count())

    def test_partial_update_team_members_only(self) -> None:
        """Verify a team can be partially updated by changing only the members."""

        update_data = {
            "members": [
                {"user": self.user2, "role": TeamMembership.Role.ADMIN},
                {"user": self.user3, "role": TeamMembership.Role.MEMBER},
            ]
        }
        serializer = TeamSerializer(instance=self.team, partial=True)
        updated_team = serializer.update(self.team, update_data)

        # Name should remain unchanged
        self.assertEqual("Old Team Name", updated_team.name)
        self.assertEqual(3, updated_team.members.count())

        # Unspecified membership roles remain unchanged and specified roles are created/updated
        self.assertEqual(TeamMembership.Role.OWNER, updated_team.members.get(user=self.user1).role)
        self.assertEqual(TeamMembership.Role.ADMIN, updated_team.members.get(user=self.user2).role)
        self.assertEqual(TeamMembership.Role.MEMBER, updated_team.members.get(user=self.user3).role)
