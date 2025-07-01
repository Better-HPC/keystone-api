"""Unit tests for the `should_notify_upcoming_expiration` function."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.allocations.models import AllocationRequest
from apps.allocations.tasks import should_notify_upcoming_expiration
from apps.notifications.models import Preference
from apps.users.models import Team, User


class ShouldNotifyUpcomingExpirationMethod(TestCase):
    """Test the determination of whether an expiry threshold notification should be issued."""

    def setUp(self) -> None:
        """Set up test data."""

        self.user = User.objects.create_user(
            username='testuser',
            password='foobar123!',
            date_joined=datetime(2020, 1, 1, tzinfo=timezone.utc)
        )

        self.team = Team.objects.create()
        self.request = AllocationRequest.objects.create(team=self.team, expire=date.today() + timedelta(days=15))

    def test_false_if_request_does_not_expire(self) -> None:
        """Verify the return value is `False` if the request does not expire."""

        self.request.expire = None
        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_upcoming_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*Request does not expire.')

    def test_false_if_request_already_expired(self) -> None:
        """Verify the return value is `False` if the request has already expired."""

        self.request.expire = date.today()
        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_upcoming_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*Request has already expired.')

    def test_false_if_no_threshold_reached(self) -> None:
        """Verify the return value is `False` if no threshold is reached."""

        # Set notification threshold smaller than days to expiration
        Preference.objects.create(user=self.user, request_expiry_thresholds=[5])

        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_upcoming_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*No notification threshold has been hit yet.')

    def test_false_if_user_recently_joined(self) -> None:
        """Verify the return value is `False` if the user recently joined."""

        # Set account creation date after notification threshold
        self.user.date_joined = datetime.now()
        Preference.objects.create(user=self.user, request_expiry_thresholds=[15])

        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_upcoming_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*User account created after notification threshold.')

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_notification_filter: Mock) -> None:
        """Verify the return value is `False` if a notification has already been issued."""

        # Set notification threshold equal to the days until expiration
        Preference.objects.create(user=self.user, request_expiry_thresholds=[15])
        mock_notification_filter.return_value.exists.return_value = True

        with self.assertLogs('apps.allocations.tasks', level='DEBUG') as log:
            self.assertFalse(should_notify_upcoming_expiration(self.user, self.request))
            self.assertRegex(log.output[-1], '.*Notification already sent for threshold.')

    def test_true_if_new_notification(self) -> None:
        """Verify the return value is `True` if a notification threshold has been hit."""

        # Set notification threshold equal to the days until expiration
        Preference.objects.create(user=self.user, request_expiry_thresholds=[15])
        self.assertTrue(should_notify_upcoming_expiration(self.user, self.request))
