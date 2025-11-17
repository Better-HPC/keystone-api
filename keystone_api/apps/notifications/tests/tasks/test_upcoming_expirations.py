"""Tests for the `tasks.upcoming_expirations` module."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.factories import PreferenceFactory
from apps.notifications.tasks.upcoming_expirations import should_notify_upcoming_expiration
from apps.users.factories import UserFactory


class ShouldNotifyUpcomingExpirationMethod(TestCase):
    """Test the determination of whether a notification should be issued for an upcoming expiration."""

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_filter: Mock) -> None:
        """Verify returns `False` if a notification has already been issued."""

        mock_filter.return_value.exists.return_value = True

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(submitter=user, expire=date.today() + timedelta(days=15))
        PreferenceFactory(user=user, request_expiry_thresholds=[5])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_true_if_new_notification(self) -> None:
        """Verify returns `True` if a notification threshold has been hit."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(submitter=user, expire=date.today() + timedelta(days=5))
        PreferenceFactory(user=user, request_expiry_thresholds=[15])

        self.assertTrue(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_does_not_expire(self) -> None:
        """Verify returns `False` if the request does not expire."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(submitter=user, expire=None)
        PreferenceFactory(user=user, request_expiry_thresholds=[15])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_already_expired(self) -> None:
        """Verify returns `False` if the request has already expired."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(submitter=user, expire=date.today())
        PreferenceFactory(user=user, request_expiry_thresholds=[15])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_no_threshold_reached(self) -> None:
        """Verify returns `False` if no threshold has been reached."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(submitter=user, expire=date.today() + timedelta(days=15))
        PreferenceFactory(user=user, request_expiry_thresholds=[5])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_user_recently_joined(self) -> None:
        """Verify returns `False` if the user is new."""

        user = UserFactory(date_joined=timezone.now())
        request = AllocationRequestFactory(submitter=user, expire=date.today() + timedelta(days=15))
        PreferenceFactory(user=user, request_expiry_thresholds=[15])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_recently_activated(self) -> None:
        """Verify returns `False` if the active date is after the notification threshold."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))

        # Expiring soon enough to hit the threshold
        request = AllocationRequestFactory(
            submitter=user,
            expire=date.today() + timedelta(days=10),
            active=date.today()  # active too recently
        )

        # Threshold of 15 days → threshold date = today - 15
        PreferenceFactory(user=user, request_expiry_thresholds=[15])

        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )
