"""Unit tests for the `PreferenceSerializer` class."""

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from apps.notifications.serializers import PreferenceSerializer
from apps.users.factories import UserFactory
from apps.users.models import User


class ValidateUserMethod(TestCase):
    """Test validation of the `user` field."""

    def setUp(self) -> None:
        """Create dummy user accounts and test data."""

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

    @staticmethod
    def _create_serializer(requesting_user: User, data: dict) -> PreferenceSerializer:
        """Return a serializer instance with the given user and data.

        Args:
            requesting_user: The authenticated user tied to the serialized HTTP request.
            data: The data to be serialized.
        """

        django_request = RequestFactory().post('/reviews/', data)
        api_request = Request(django_request)
        api_request.user = requesting_user
        return PreferenceSerializer(data=data, context={'request': api_request})

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
