"""Unit tests for the `PrivilegeUserSerializer` class."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.users.serializers import PrivilegedUserSerializer

User = get_user_model()


class ValidateMethod(TestCase):
    """Test record validation via the `validate` method."""

    def setUp(self) -> None:
        """Define dummy user data."""

        self.user_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'email': 'testuser@example.com',
        }

    def test_password_hashed_on_create(self) -> None:
        """Verify the password is hashed when validating a record creation."""

        serializer = PrivilegedUserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(check_password('Password123!', serializer.validated_data['password']))

    def test_password_is_hashed_on_update(self) -> None:
        """Verify the password is hashed when validating a record update."""

        user = User.objects.create_user(username='existing', password='OldPassword123!')
        serializer = PrivilegedUserSerializer(user, data={'password': 'NewPassword456!'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(check_password('NewPassword456!', serializer.validated_data['password']))

    def test_error_for_invalid_password(self) -> None:
        """Verify an invalid password raises a `ValidationError`."""

        self.user_data['password'] = '123'  # Too short
        serializer = PrivilegedUserSerializer(data=self.user_data)
        with self.assertRaises(DRFValidationError):
            serializer.is_valid(raise_exception=True)

    def test_error_for_missing_password(self) -> None:
        """Verify validation fails when a password is not provided."""

        user_data_no_password = self.user_data.copy()
        user_data_no_password.pop('password')
        self.assertNotIn('password', user_data_no_password)

        serializer = PrivilegedUserSerializer(data=user_data_no_password)
        self.assertFalse(serializer.is_valid())
