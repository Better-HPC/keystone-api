"""Unit tests for the `User` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.models import User


class UserModelRegistration(TestCase):
    """Test the registration of the model with the Django authentication system."""

    def test_registered_as_default_user_model(self) -> None:
        """Verify the `User` class is returned by the built-in `get_user_model` method."""

        self.assertIs(User, get_user_model())


class SaveMethod(TestCase):
    """Test the creation of users via the `save` method."""

    def setUp(self) -> None:
        """Set up a test user instance."""

        self.username = 'testuser'
        self.email = 'testuser@example.com'
        self.user = User(
            username=self.username,
            email=self.email,
            password='password123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self) -> None:
        """Verify `User` instances are successfully created."""

        self.user.save()
        self.assertIsNotNone(self.user.pk)
        self.assertEqual(self.user.username, self.username)
        self.assertEqual(self.user.email, self.email)

    def test_profile_image_generation(self) -> None:
        """Verify a profile image is generated if one does not exist."""

        self.assertFalse(self.user.profile_image)
        self.user.save()  # Saving the user should trigger image generation

        self.assertTrue(self.user.profile_image)
        self.assertTrue(self.user.profile_image.name.endswith('.png'))
        self.assertTrue(self.user.profile_image.name.endswith('.png'))

    def test_image_is_unique(self) -> None:
        """Verify the generated profile image is unique for different users."""

        user1 = User(username='user1')
        user2 = User(username='user2')

        user1.save()
        user2.save()

        self.assertNotEqual(user1.profile_image.read(), user2.profile_image.read())

    def test_existing_image_not_overwritten(self) -> None:
        """Verify profile images are not overwritten by default."""

        self.user.save()
        original_image = self.user.profile_image

        self.user.save()
        self.assertEqual(self.user.profile_image.name, original_image.name)
