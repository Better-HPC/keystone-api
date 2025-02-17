"""Unit tests for the `should_notify_past_expiration` function."""

from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.allocations.models import AllocationRequest
from apps.allocations.tasks import should_notify_past_expiration
from apps.notifications.models import Preference
from apps.users.models import Team, User


class ShouldNotifyPastExpirationMethod(TestCase):
    """Test the determination of whether an expiration notification should be issued."""

    def setUp(self) -> None:
        """Set up test data."""

        self.user = User.objects.create_user(username='testuser', password='foobar123!')
        self.team = Team.objects.create()
        self.request = AllocationRequest.objects.create(team=self.team, expire=date.today())

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_notification_filter: Mock) -> None:
        """Verify the return value is `False` if a notification has already been issued."""

        mock_notification_filter.return_value.exists.return_value = True
        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_past_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*Notification already sent.')

    def test_false_if_disabled_in_preferences(self) -> None:
        """Verify the return value is `False` if expiry notifications are disabled in preferences."""

        Preference.objects.create(user=self.user, notify_on_expiration=False)
        self.assertFalse(should_notify_past_expiration(self.user, self.request))

    def test_true_if_new_notification(self) -> None:
        """Verify the return value is `True` if a notification has not been issued yet."""

        self.assertTrue(should_notify_past_expiration(self.user, self.request))
