"""Unit tests for the `Logout` class."""

from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from apps.authentication.views import LogoutView


class PostMethod(TestCase):
    """Test HTTP request handling by the `post` method."""

    def setUp(self) -> None:
        """Create a new view instance."""

        self.view = LogoutView()
        self.factory = RequestFactory()

    @patch('apps.authentication.views.logout')
    def test_logout_triggered(self, mock_logout: Mock) -> None:
        """Verify the system logout method is called."""

        request = self.factory.post('/logout/')

        self.view.post(request)
        mock_logout.assert_called_with(request)
