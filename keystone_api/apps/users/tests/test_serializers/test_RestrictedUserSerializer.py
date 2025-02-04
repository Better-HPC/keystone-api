"""Unit tests for the `RestrictedUserSerializer` class."""

from django.test import TestCase

from apps.users.serializers import RestrictedUserSerializer


class CreateMethod(TestCase):
    """Test record creation via the `create` method."""

    def test_create_raises_not_permitted(self) -> None:
        """Verify the create method raises a `RuntimeError`."""

        serializer = RestrictedUserSerializer()
        with self.assertRaises(RuntimeError):
            serializer.create({'username': 'testuser', 'password': 'Password123!'})
