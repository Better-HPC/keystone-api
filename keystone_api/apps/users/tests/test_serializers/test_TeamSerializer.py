"""Unit tests for the `TeamSerializer` class."""

from django.test import TestCase

from apps.users.models import Team, TeamMembership, User
from apps.users.serializers import TeamSerializer


class CreateRecords(TestCase):
    """Test the creation of records via the `create` method`."""

    def test_create_with_membership(self) -> None:
        """Test creating a team record with membership data."""

        # User accounts to enroll in team membership
        user1 = User.objects.create(username='User 1')
        user2 = User.objects.create(username='User 2')

        # Valid record data, typically from an incoming HTTP request
        request_data = {
            'name': 'Team A',
            'is_active': True,
            'membership': [
                {'user': 1, 'role': TeamMembership.Role.MEMBER},
                {'user': 2, 'role': TeamMembership.Role.OWNER}
            ]
        }

        serializer = TeamSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        # Verify the created team record
        team = serializer.create(serializer.validated_data)
        self.assertEqual(team.name, request_data['name'])
        self.assertEqual(team.is_active, request_data['is_active'])
        self.assertEqual(team.teammembership_set.count(), len(request_data['membership']))

        # Verify values for the created memberships
        memberships = team.teammembership_set.all()
        self.assertEqual(memberships[0].user, user1)
        self.assertEqual(memberships[0].role, TeamMembership.Role.MEMBER)
        self.assertEqual(memberships[1].user, user2)
        self.assertEqual(memberships[1].role, TeamMembership.Role.OWNER)

    def test_create_without_membership(self) -> None:
        """Test creating a team record without membership data."""

        self.serializer = TeamSerializer(data={
            'name': 'Team B',
            'is_active': False,
        })

        self.serializer.is_valid(raise_exception=True)
        team = self.serializer.create(self.serializer.validated_data)

        self.assertEqual(team.name, 'Team B')
        self.assertEqual(team.is_active, False)
        self.assertEqual(team.teammembership_set.count(), 0)


class UpdateRecords(TestCase):
    """Test the updating of records via the `update` method`."""

    def setUp(self) -> None:
        """Create an initial team record to modify dering tests."""

        self.user = User.objects.create(username='User 1')
        self.team = Team.objects.create(name='Old Team Name', is_active=True)
        self.membership = TeamMembership.objects.create(team=self.team, user=self.user, role=TeamMembership.Role.MEMBER)

    def test_update_with_membership(self) -> None:
        """Test updating a team record while also changing user membership roles."""

        # Define the new user role to update to
        new_role = TeamMembership.Role.OWNER
        self.assertNotEqual(new_role, self.membership.role)

        valid_data = {
            'name': 'Updated Team Name',
            'is_active': False,
            'membership': [
                {'user': 1, 'role': new_role},
            ]
        }

        serializer = TeamSerializer(instance=self.team, data=valid_data)
        serializer.is_valid(raise_exception=True)
        updated_team = serializer.update(self.team, serializer.validated_data)

        # Check team was updated
        self.assertEqual(updated_team.name, valid_data['name'])
        self.assertEqual(updated_team.is_active, valid_data['is_active'])
        self.assertEqual(updated_team.teammembership_set.count(), 1)

        # Check membership was updated
        new_membership = updated_team.teammembership_set.get(user=self.user)
        self.assertEqual(new_membership.user, self.user)
        self.assertEqual(new_membership.role, new_role)

    def test_update_without_membership(self) -> None:
        """Test updating a team record without changing user membership."""

        valid_data = {
            'name': 'Another Updated Team Name',
            'is_active': True,
        }

        serializer = TeamSerializer(instance=self.team, data=valid_data)
        serializer.is_valid(raise_exception=True)
        updated_team = serializer.update(self.team, serializer.validated_data)

        # Check team was updated
        self.assertEqual(updated_team.name, valid_data['name'])
        self.assertEqual(updated_team.is_active, valid_data['is_active'])
        self.assertEqual(updated_team.teammembership_set.count(), 1)

        # Check membership was NOT updated
        membership = updated_team.teammembership_set.first()
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, TeamMembership.Role.MEMBER)
