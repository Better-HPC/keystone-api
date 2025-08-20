"""Unit tests for the `UserViewSet` class."""

from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.users.factories import UserFactory
from apps.users.serializers import PrivilegedUserSerializer, RestrictedUserSerializer
from apps.users.views import UserViewSet


class GetSerializerClassMethod(TestCase):
    """Test the correct serializer is returned by the `get_serializer_class` method."""

    def setUp(self) -> None:
        """Create user accounts for testing"""

        self.regular_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

    def test_get_serializer_class_for_staff_user(self) -> None:
        """Verify the `PrivilegeUserSerializer` serializer is returned for a staff user."""

        request = Request(RequestFactory().get('/users/'))
        request.user = self.staff_user
        view = UserViewSet(request=request)

        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, PrivilegedUserSerializer)

    def test_get_serializer_class_for_regular_user(self) -> None:
        """Verify the `RestrictedUserSerializer` serializer is returned for a generic user."""

        request = Request(RequestFactory().get('/users/'))
        request.user = self.regular_user
        view = UserViewSet(request=request)

        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, RestrictedUserSerializer)
