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
        """Create a new view instance."""

        self.view = WhoAmIView()
        self.factory = RequestFactory()
        self.user = User.objects.create(username='testuser', password='password')

    def test_authenticated_user(self) -> None:
        """Verify authenticated users are returned their own metadata."""

        request = self.factory.get('/whoami/')
        request.user = self.user

        expected_data = RestrictedUserSerializer(request.user).data
        response = self.view.get(request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_data, response.data)
