"""Unit tests for the `AllocationRequestSerializer` class."""

from django.test import RequestFactory, TestCase

from apps.allocations.factories import AllocationRequestFactory, CommentFactory
from apps.allocations.serializers import AllocationRequestSerializer
from apps.users.factories import UserFactory
from apps.users.models import User


class GetCommentsMethod(TestCase):
    """Test the filtering of returned allocation request comments."""

    def setUp(self) -> None:
        """Setup mock data."""

        self.allocation_request = AllocationRequestFactory()

        self.public_comment = CommentFactory(
            request=self.allocation_request, private=False, content='Public comment'
        )

        self.private_comment = CommentFactory(
            request=self.allocation_request, private=True, content='Private comment'
        )

    @staticmethod
    def _create_context(user: User) -> dict:
        """Create serializer context with a request containing the given user."""

        request = RequestFactory().get('/fake-url/')
        request.user = user
        return {'request': request}

    def test_filters_private_comments_for_non_staff_user(self) -> None:
        """Verify non-staff users are only returned public comments."""

        user = UserFactory(is_staff=False)
        context = self._create_context(user=user)
        serializer = AllocationRequestSerializer(context=context)

        result = serializer.get__comments(self.allocation_request)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['content'], 'Public comment')

    def test_returns_all_comments_for_staff_user(self) -> None:
        """Verify staff users are returned public and private comments."""

        user = UserFactory(is_staff=True)
        context = self._create_context(user=user)
        serializer = AllocationRequestSerializer(context=context)

        result = serializer.get__comments(self.allocation_request)

        self.assertEqual(len(result), 2)

    def test_filters_private_comments_when_user_is_none(self) -> None:
        """Verify private comments are excluded when the requesting user is `None`."""

        context = self._create_context(user=None)
        serializer = AllocationRequestSerializer(context=context)

        result = serializer.get__comments(self.allocation_request)

        self.assertEqual(len(result), 1)

    def test_filters_private_comments_when_request_missing(self) -> None:
        """Verify private comments are excluded when the `request` object is `None`."""

        serializer = AllocationRequestSerializer(context={})

        result = serializer.get__comments(self.allocation_request)

        self.assertEqual(len(result), 1)

    def test_filters_private_comments_when_no_context(self) -> None:
        """Verify private comments are excluded when request context is empty."""

        serializer = AllocationRequestSerializer()

        result = serializer.get__comments(self.allocation_request)

        self.assertEqual(len(result), 1)
