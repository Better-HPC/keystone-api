"""Unit tests for the `PreferenceSerializer` class."""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.notifications.serializers import PreferenceSerializer
from apps.users.models import User


class ValidateUserMethod(TestCase):
    """Test validation of the `user` field."""

    def setUp(self) -> None:
        """Create dummy user accounts and test data."""

        self.user1 = User.objects.create_user(username='testuser1', password='foobar123!')
        self.user2 = User.objects.create_user(username='testuser2', password='foobar123!')
        self.staff_user = User.objects.create_superuser(username='staff', password='foobar123!')

    @staticmethod
    def _create_serializer(requesting_user: User, data: dict) -> PreferenceSerializer:
        """Return a serializer instance with the given user and data.

        Args:
            requesting_user: The authenticated user tied to the serialized HTTP request.
            data: The data to be serialized.
        """

        request = APIRequestFactory().post('/reviews/', data)
        request.user = requesting_user
        return PreferenceSerializer(data=data, context={'request': request})

    def test_field_matches_submitter(self) -> None:
        """Verify validation passes when the user field equals the user submitting the HTTP request."""

        serializer = self._create_serializer(self.user1, {'user': self.user1.id})
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_different_field_from_submitter(self) -> None:
        """Verify validation fails when the user field is different from the user submitting the HTTP request."""

        serializer = self._create_serializer(self.user2, {'user': self.user1.id})
        with self.assertRaisesRegex(ValidationError, "User field cannot be set to a different user than the request submitter."):
            serializer.is_valid(raise_exception=True)

    def test_staff_override_validation(self) -> None:
        """Verify staff users bypass validation."""

        serializer = self._create_serializer(self.staff_user, {'user': self.user1.id})
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_field_is_optional(self) -> None:
        """Verify the user field is optional."""

        serializer = self._create_serializer(self.staff_user, {})
        self.assertTrue(serializer.is_valid(raise_exception=True))
