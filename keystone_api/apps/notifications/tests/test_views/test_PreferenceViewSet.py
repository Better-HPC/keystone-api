"""Unit tests for the `PreferenceViewSet` class."""

from django.test import RequestFactory, TestCase
from rest_framework import status

from apps.notifications.views import PreferenceViewSet
from apps.users.models import User


class CreateMethod(TestCase):
    """Test the creation of new records via the `create` method."""

    def setUp(self) -> None:
        """Load test data from fixtures."""

        self.user = User.objects.create_user(username='testuser', password='password123!')

    @staticmethod
    def _create_viewset_with_post(data: dict, user: User) -> PreferenceViewSet:
        """Create a new viewset instance with a mock POST request."""

        request = RequestFactory().post('/dummy-endpoint/')
        request.data = data
        request.user = user

        viewset = PreferenceViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        return viewset

    def test_missing_user_fields(self) -> None:
        """Verify the reviewer field is automatically set to the current user."""

        viewset = self._create_viewset_with_post(dict(), self.user)
        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)

    def test_provided_user_field(self) -> None:
        """Verify the reviewer field in the request data is respected if provided."""

        viewset = self._create_viewset_with_post({'user': self.user.id}, self.user)
        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
