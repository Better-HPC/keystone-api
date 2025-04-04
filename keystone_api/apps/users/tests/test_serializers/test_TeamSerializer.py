"""Unit tests for the `TeamSerializer` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.models import Membership, Team
from apps.users.serializers import TeamSerializer

User = get_user_model()


class CreateMethod(TestCase):
    """Test record creation via the `create`  method."""

    def setUp(self) -> None:
        """Define dummy team data."""

        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

    def test_create_team_with_members(self) -> None:
        """Verify a team is created with the correct members."""

        team_data = {
            "name": "Test Team",
            "membership": [
                {"user": self.user1.pk, "role": Membership.Role.ADMIN},
                {"user": self.user2.pk, "role": Membership.Role.MEMBER},
            ],
        }

        serializer = TeamSerializer(data=team_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.create(serializer.validated_data)

        self.assertEqual("Test Team", team.name)
        self.assertEqual(2, team.membership.count())
        self.assertEqual(Membership.Role.ADMIN, team.membership.get(user=self.user1).role)
        self.assertEqual(Membership.Role.MEMBER, team.membership.get(user=self.user2).role)

    def test_create_team_without_members(self) -> None:
        """Verify a team is created successfully when members are specified."""

        team_data = {"name": "Test Team"}

        serializer = TeamSerializer(data=team_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.create(serializer.validated_data)

        self.assertEqual(team_data["name"], team.name)
        self.assertEqual(0, team.membership.count())


class UpdateMethod(TestCase):
    """Test record updating via the `update`  method."""

    def setUp(self) -> None:
        """Define dummy team and membership data."""

        self.team = Team.objects.create(name="Old Team Name")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")

        Membership.objects.create(team=self.team, user=self.user1, role=Membership.Role.OWNER)
        Membership.objects.create(team=self.team, user=self.user2, role=Membership.Role.MEMBER)

    def test_update_team(self) -> None:
        """Verify a team is updated correctly with new members and name."""

        update_data = {
            "name": "New Team Name",
            "membership": [
                {"user": self.user1, "role": Membership.Role.ADMIN},
                {"user": self.user3, "role": Membership.Role.MEMBER},
            ],
        }

        serializer = TeamSerializer(instance=self.team)
        updated_team = serializer.update(self.team, update_data)

        # Make sure the team name and membership is updated
        self.assertEqual(updated_team.name, "New Team Name")
        self.assertEqual(Membership.Role.ADMIN, updated_team.membership.get(user=self.user1).role)
        self.assertEqual(Membership.Role.MEMBER, updated_team.membership.get(user=self.user3).role)

        # Old memberships are removed
        self.assertEqual(updated_team.membership.count(), 2)
        self.assertFalse(updated_team.membership.filter(user=self.user2).exists())

    def test_partial_update_team_name_only(self) -> None:
        """Verify a team can be partially updated by changing only the name."""

        update_data = {"name": "Partially Updated Team"}
        serializer = TeamSerializer(instance=self.team, partial=True)
        updated_team = serializer.update(self.team, update_data)

        self.assertEqual(updated_team.name, "Partially Updated Team")
        self.assertEqual(2, updated_team.membership.count())

    def test_partial_update_team_members_only(self) -> None:
        """Verify a team can be partially updated by changing only the members."""

        update_data = {
            "membership": [
                {"user": self.user2, "role": Membership.Role.ADMIN},
                {"user": self.user3, "role": Membership.Role.MEMBER},
            ]
        }
        serializer = TeamSerializer(instance=self.team, partial=True)
        updated_team = serializer.update(self.team, update_data)

        # Name should remain unchanged
        self.assertEqual("Old Team Name", updated_team.name)
        self.assertEqual(3, updated_team.membership.count())

        # Unspecified membership roles remain unchanged and specified roles are created/updated
        self.assertEqual(Membership.Role.OWNER, updated_team.membership.get(user=self.user1).role)
        self.assertEqual(Membership.Role.ADMIN, updated_team.membership.get(user=self.user2).role)
        self.assertEqual(Membership.Role.MEMBER, updated_team.membership.get(user=self.user3).role)
