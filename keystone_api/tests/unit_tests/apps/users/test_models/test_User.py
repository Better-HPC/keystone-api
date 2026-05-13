"""Unit tests for the `User` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.factories import UserFactory
from apps.users.models import User


class UserModelRegistration(TestCase):
    """Test the registration of the model with the Django authentication system."""

    def test_registered_as_default_user_model(self) -> None:
        """Verify the `User` class is returned by the built-in `get_user_model` method."""

        self.assertIs(User, get_user_model())


class AbbreviationProperty(TestCase):
    """Test the generation of user abbreviations."""

    def test_missing_first_and_last(self) -> None:
        """Verify the username is abbreviated when first and last name are missing."""

        user = UserFactory(username="user1", first_name=None, last_name=None)
        self.assertEqual("US", user.abbreviation)

    def test_missing_first(self) -> None:
        """Verify the username is abbreviated when first name is missing."""

        user = UserFactory(username="user1", first_name=None, last_name="Last")
        self.assertEqual("US", user.abbreviation)

    def test_missing_last(self) -> None:
        """Verify the first name is abbreviated when last name is missing."""

        user = UserFactory(username="user1", first_name="First", last_name=None)
        self.assertEqual("F", user.abbreviation)

    def test_has_first_and_last(self) -> None:
        """Verify the full name is abbreviated when first and last name are both defined."""

        user = UserFactory(username="user1", first_name="First", last_name="Last")
        self.assertEqual("FL", user.abbreviation)


class DisplayNameProperty(TestCase):
    """Test the generation of user display names."""

    def test_missing_first_and_last(self) -> None:
        """Verify the username is returned when first and last name are missing."""

        user = UserFactory(username="user1", first_name=None, last_name=None)
        self.assertEqual(user.username, user.display_name)

    def test_missing_first(self) -> None:
        """Verify the username is returned when first name is missing."""

        user = UserFactory(username="user1", first_name=None, last_name="Last")
        self.assertEqual(user.username, user.display_name)

    def test_missing_last(self) -> None:
        """Verify the first name is returned when last name is missing."""

        user = UserFactory(username="user1", first_name="First", last_name=None)
        self.assertEqual(user.first_name, user.display_name)

    def test_has_first_and_last(self) -> None:
        """Verify the first and last name is returned when first and last name are both defined."""

        user = UserFactory(username="user1", first_name="First", last_name="Last")
        self.assertEqual(f"{user.first_name} {user.last_name}", user.display_name)
