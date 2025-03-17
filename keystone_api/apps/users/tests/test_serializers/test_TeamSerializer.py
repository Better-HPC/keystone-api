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

    def test_create_team_with_members(self) -> None:
        """Verify a team is created with the correct members."""

        serializer = TeamSerializer(data=self.team_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertEqual(team.name, "Test Team")
        self.assertEqual(team.teammembership_set.count(), 2)
        self.assertEqual(team.teammembership_set.get(user=self.user1).role, TeamMembership.Role.ADMIN)
        self.assertEqual(team.teammembership_set.get(user=self.user2).role, TeamMembership.Role.MEMBER)


class UpdateMethod(TestCase):
    """Test case for the `update` method of `TeamSerializer`."""

    def setUp(self) -> None:
        """Define dummy team and membership data."""

        self.team = Team.objects.create(name="Old Team Name")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.user3 = User.objects.create(username="user3")

        TeamMembership.objects.create(team=self.team, user=self.user1, role="OW")
        TeamMembership.objects.create(team=self.team, user=self.user2, role=TeamMembership.Role.MEMBER)

        self.update_data = {
            "name": "New Team Name",
            "members": [
                {"user": self.user1, "role": TeamMembership.Role.ADMIN},
                {"user": self.user3, "role": TeamMembership.Role.MEMBER},
            ],
        }

    def test_update_team_with_new_name_and_members(self) -> None:
        """Verify a team is updated correctly with new members and name."""

        serializer = TeamSerializer(instance=self.team, data=self.update_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_team = serializer.save()

        self.assertEqual(updated_team.name, "New Team Name")
        self.assertEqual(updated_team.teammembership_set.count(), 2)
        self.assertEqual(updated_team.teammembership_set.get(user=self.user1).role, TeamMembership.Role.ADMIN)
        self.assertEqual(updated_team.teammembership_set.get(user=self.user3).role, TeamMembership.Role.MEMBER)
        self.assertFalse(updated_team.teammembership_set.filter(user=self.user2).exists())
