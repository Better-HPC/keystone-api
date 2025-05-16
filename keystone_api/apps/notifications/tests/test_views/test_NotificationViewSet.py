"""Unit tests for the `NotificationViewSet` class."""

from django.test import RequestFactory, TestCase

from apps.notifications.models import Notification
from apps.notifications.views import NotificationViewSet
from apps.users.models import User


class GetQuerysetMethod(TestCase):
    """Test the scope of database queries returned by the `get_queryset` method."""

    fixtures = ['testing_common.yaml']

    def test_get_queryset_returns_user_only(self) -> None:
        """Verify users can only access their own notifications."""

        user = User.objects.get(username='member_1')

        viewset = NotificationViewSet()
        viewset.request = RequestFactory()
        viewset.request.user = user

        queryset = viewset.get_queryset()
        expected_queryset = Notification.objects.filter(user=user)
        self.assertQuerySetEqual(queryset, expected_queryset, ordered=False)
