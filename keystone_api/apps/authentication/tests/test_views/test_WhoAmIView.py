"""Unit tests for the `WhoAmIView` class."""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework import status

from apps.authentication.views import WhoAmIView
from apps.users.serializers import RestrictedUserSerializer

User = get_user_model()


class GetMethod(TestCase):
    """Test HTTP request handling by the `get` method."""

    def setUp(self) -> None:
        """Create a view instance and HTTP request factory."""

        self.factory = RequestFactory()
        self.view = WhoAmIView.as_view()
        self.user = User.objects.create(username='testuser', password='password')

    def test_get_authenticated_user(self) -> None:
        """Verify user data is returned for an authenticated user."""

        request = self.factory.get('/whoami/')
        request.user = self.user

        response = self.view(request)
        expected_data = RestrictedUserSerializer(self.user).data

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_data, response.data)
