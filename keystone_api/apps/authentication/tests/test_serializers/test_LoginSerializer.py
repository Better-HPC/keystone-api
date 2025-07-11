"""Unit tests for the `LoginSerializer` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.authentication.serializers import LoginSerializer

User = get_user_model()


class Validation(TestCase):
    """Test the validation of user credentials."""

    def setUp(self) -> None:
        """Create a user account to test authentication with."""

        self.password = 'securepass'
        self.user = User.objects.create_user(username='testuser', password=self.password)
        self.request = APIRequestFactory().post('/login/')

    def test_valid_credentials(self) -> None:
        """Verify valid user credentials pass validation."""

        data = {'username': self.user.username, 'password': self.password}
        serializer = LoginSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)

    def test_invalid_credentials(self) -> None:
        """Verify invalid user credentials fail validation."""

        data = {'username': self.user.username, 'password': 'wrongpass'}
        serializer = LoginSerializer(data=data, context={'request': self.request})
        with self.assertRaisesRegex(ValidationError, 'Invalid username or password.'):
            serializer.is_valid(raise_exception=True)

    def test_inactive_user(self) -> None:
        """Verify inactive users fail validation even with correct credentials."""

        self.user.is_active = False
        self.user.save()

        data = {'username': self.user.username, 'password': self.password}
        serializer = LoginSerializer(data=data, context={'request': self.request})
        with self.assertRaisesRegex(ValidationError, 'Invalid username or password.'):
            serializer.is_valid(raise_exception=True)

    def test_password_whitespace_preserved(self) -> None:
        """Ensure passwords with whitespace are not stripped during validation."""

        # Create a user with whitespace in the password
        password_with_spaces = '  spacedpass  '
        user_with_spaces = User.objects.create_user(username='whitespaceuser', password=password_with_spaces)

        # Attempt login with exact password (should succeed)
        data = {'username': user_with_spaces.username, 'password': password_with_spaces}
        serializer = LoginSerializer(data=data, context={'request': self.request})
        serializer.is_valid()

        self.assertEqual(serializer.validated_data['user'], user_with_spaces)
        self.assertTrue(serializer.is_valid())

        # Attempt login with stripped password (should fail)
        data_stripped = {'username': user_with_spaces.username, 'password': password_with_spaces.strip()}
        serializer = LoginSerializer(data=data_stripped, context={'request': self.request})
        with self.assertRaisesRegex(ValidationError, 'Invalid username or password.'):
            serializer.is_valid(raise_exception=True)
