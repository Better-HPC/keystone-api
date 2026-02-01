"""Unit tests for the `CommentSerializer` class."""

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from apps.allocations.factories import AllocationRequestFactory
from apps.allocations.models import Comment
from apps.allocations.serializers import CommentSerializer
from apps.users.factories import UserFactory


class ValidateMethod(TestCase):
    """Test the validation of record values."""

    def setUp(self) -> None:
        """Initialize test fixtures."""

        self.normal_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.alloc_request = AllocationRequestFactory()

    @staticmethod
    def _user_post_request(user) -> Request:
        """Create an HTTP request originating from the given user.

        Args:
            user: The user to create the request from.

        Returns:
            An HTTP POST request against the `/dummy/` endpoint.
        """

        drf_request = Request(RequestFactory().post('/dummy/'))
        drf_request.user = user
        return drf_request

    def test_non_staff_create_private(self) -> None:
        """Verify non-staff users cannot create comments with `private=True`."""

        request = self._user_post_request(self.normal_user)
        data = {
            'request': self.alloc_request.pk,
            'user': self.normal_user.pk,
            'private': True,
            'content': 'User private comment'
        }

        serializer = CommentSerializer(data=data, context={'request': request})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_staff_create_private(self) -> None:
        """Verify staff users can create comments with `private=True`."""

        request = self._user_post_request(self.staff_user)
        data = {
            'request': self.alloc_request.pk,
            'user': self.staff_user.pk,
            'private': True,
            'content': 'Staff private comment'
        }

        serializer = CommentSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_staff_update_to_private(self) -> None:
        """Verify non-staff users cannot update the `private` field from `False` to `True`."""

        # Initialize a public comment
        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.normal_user,
            private=False,
            content='Original comment'
        )

        # Update a comment to private
        data = {'private': True}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.normal_user)}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_non_staff_update_to_public(self) -> None:
        """Verify non-staff users cannot update the `private` field from `True` to `False`."""

        # Initialize a private comment
        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.normal_user,
            private=True,
            content='Staff private'
        )

        # Update a comment to public
        data = {'private': False}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.normal_user)}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_staff_update_to_private(self) -> None:
        """Verify staff users can update the `private` field from `False` to `True`."""

        # Initialize a public comment
        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.staff_user,
            private=False,
            content='Original comment'
        )

        # Update a comment to private
        data = {'private': True}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.staff_user)}
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_staff_update_set_public(self) -> None:
        """Verify staff users can update the `private` field from `True` to `False`."""

        # Initialize a private comment
        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.staff_user,
            private=True,
            content='Staff private'
        )

        # Update a comment to public
        data = {'private': False}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.staff_user)}
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_non_staff_update_private_content(self) -> None:
        """Verify non-staff users cannot update comment contents when `private=True`."""

        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.normal_user,
            private=True,
            content='Staff private'
        )

        data = {'content': "This is new content"}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.normal_user)}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_staff_update_private_content(self) -> None:
        """Verify staff users can update comment contents when `private=True`."""

        comment = Comment.objects.create(
            request=self.alloc_request,
            user=self.staff_user,
            private=True,
            content='Staff private'
        )

        data = {'content': "This is new content"}
        serializer = CommentSerializer(
            instance=comment,
            data=data,
            partial=True,
            context={'request': self._user_post_request(self.staff_user)}
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))
