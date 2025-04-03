"""Unit tests for the `PrivilegeUserSerializer` class."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.users.models import Membership, Team
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
            "membership": [
                {"team": self.team1.pk, "role": Membership.Role.ADMIN},
                {"team": self.team2.pk, "role": Membership.Role.MEMBER},
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
        self.assertEqual(user.membership.count(), 2)
        self.assertEqual(user.membership.get(team=self.team1).role, Membership.Role.ADMIN)
        self.assertEqual(user.membership.get(team=self.team2).role, Membership.Role.MEMBER)

    def test_create_user_without_teams(self) -> None:
        """Verify a user can be created without team memberships."""

        self.user_data.pop("membership")
        serializer = PrivilegedUserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.create(serializer.validated_data)

        self.assertEqual("testuser", user.username)
        self.assertEqual(0, user.membership.count())


class UpdateMethod(TestCase):
    """Test record updating via the `update`  method."""

    def setUp(self) -> None:
        """Define dummy team and membership data."""

        self.user = User.objects.create_user(username="old_username", email="old@example.com", password="old_password")
        self.team1 = Team.objects.create(name="Team Alpha")
        self.team2 = Team.objects.create(name="Team Beta")

        Membership.objects.create(user=self.user, team=self.team1, role=Membership.Role.OWNER)

    def test_update_user(self) -> None:
        """Verify a user is updated with correct attributes and nested memberships."""

        update_data = {
            "username": "new_username",
            "password": "new_password",
            "email": "new@example.com",
            "membership": [
                {"team": self.team2.pk, "role": Membership.Role.ADMIN},
            ],
        }

        # Update the user record
        serializer = PrivilegedUserSerializer(instance=self.user, data=update_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.update(self.user, serializer.validated_data)

        # User attributes are replaced with the given values
        self.assertEqual(update_data["username"], updated_user.username)
        self.assertEqual(update_data["email"], updated_user.email)
        self.assertTrue(updated_user.check_password(update_data["password"]))

        # All user team memberships are replaced with the provided data
        self.assertEqual(1, updated_user.membership.count())
        self.assertEqual(updated_user.membership.get(team=self.team2).role, Membership.Role.ADMIN)

    def test_partial_update_user_attributes(self) -> None:
        """Verify users can be partially updated using a subset of user attributes."""

        update_data = {
            "username": "new_username",
            "password": "new_password",
        }

        # Update the user record
        serializer = PrivilegedUserSerializer(instance=self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.update(self.user, serializer.validated_data)

        # Specified attributes are replaced with the given values
        self.assertEqual(update_data["username"], updated_user.username)
        self.assertTrue(updated_user.check_password(update_data["password"]))

        # Unspecified attributes are unchanged
        self.assertEqual("old@example.com", updated_user.email)

        # Team memberships were not specified in the update and so remain unchanged
        self.assertEqual(1, updated_user.membership.count())
        self.assertEqual(updated_user.membership.get(team=self.team1).role, Membership.Role.OWNER)

    def test_partial_update_membership_only(self) -> None:
        """Verify users can be partially updated using only team membership data."""

        update_data = {
            "membership": [
                {"team": self.team2.pk, "role": Membership.Role.MEMBER},
            ]
        }

        # Update the user record
        serializer = PrivilegedUserSerializer(instance=self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.update(self.user, serializer.validated_data)

        # Unspecified attributes are unchanged
        self.assertEqual("old_username", updated_user.username)
        self.assertEqual("old@example.com", updated_user.email)

        # Memberships specified in the update are modified. Memberships not specified are unchanged.
        self.assertEqual(2, updated_user.membership.count())
        self.assertEqual(updated_user.membership.get(team=self.team1).role, Membership.Role.OWNER)
        self.assertEqual(updated_user.membership.get(team=self.team2).role, Membership.Role.MEMBER)
