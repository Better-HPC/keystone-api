"""Unit tests for the `PrivilegeUserSerializer` class."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.users.models import Team, TeamMembership
from apps.users.serializers import PrivilegedUserSerializer

User = get_user_model()


class ValidateMethod(TestCase):
    """Test data validation via the `validate` method."""

    def setUp(self) -> None:
        """Define dummy user data."""

        self.user_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'email': 'testuser@example.com',
        }

    def test_validate_password_is_hashed(self) -> None:
        """Verify the password is hashed during validation."""

        serializer = PrivilegedUserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(check_password('Password123!', serializer.validated_data['password']))

    def test_validate_password_invalid(self) -> None:
        """Verify an invalid password raises a `ValidationError`."""

        self.user_data['password'] = '123'  # Too short
        serializer = PrivilegedUserSerializer(data=self.user_data)
        with self.assertRaises(DRFValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_without_password(self) -> None:
        """Verify validation fails when a password is not provided."""

        user_data_no_password = self.user_data.copy()
        user_data_no_password.pop('password')
        self.assertNotIn('password', user_data_no_password)

        serializer = PrivilegedUserSerializer(data=user_data_no_password)
        self.assertFalse(serializer.is_valid())


class CreateMethod(TestCase):
    """Test record creation via the `create`  method."""

    def setUp(self) -> None:
        """Define test users and teams."""

        self.team1 = Team.objects.create(name="Team Alpha")
        self.team2 = Team.objects.create(name="Team Beta")

        self.user_data = {
            "username": "testuser",
            "password": "StrongPass123!",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "teams": [
                {"team": self.team1, "role": TeamMembership.Role.ADMIN},
                {"team": self.team2, "role": TeamMembership.Role.MEMBER},
            ],
        }

    def test_create_user_with_teams(self) -> None:
        """Verify a user is created with the correct team memberships."""

        serializer = PrivilegedUserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.create(serializer.validated_data)

        # Verify user attributes
        self.assertEqual("testuser", user.username)
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertEqual("testuser@example.com", user.email)

        # Verify user roles
        self.assertEqual(user.teams.count(), 2)
        self.assertEqual(user.teams.get(team=self.team1).role, TeamMembership.Role.ADMIN)
        self.assertEqual(user.teams.get(team=self.team2).role, TeamMembership.Role.MEMBER)

    def test_create_user_without_teams(self) -> None:
        """Verify a user can be created without team memberships."""

        self.user_data.pop("teams")
        serializer = PrivilegedUserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.create(serializer.validated_data)

        self.assertEqual("testuser", user.username)
        self.assertEqual(0, user.teams.count())
