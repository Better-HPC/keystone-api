"""Tests for the `tasks.past_expirations` module."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.factories import PreferenceFactory
from apps.notifications.tasks.past_expirations import should_notify_past_expiration


class ShouldNotifyPastExpirationMethod(TestCase):
    """Test the determination of whether a notification should be issued for an expired allocation."""

    def test_true_if_expires_today(self) -> None:
        """Verify returns `True` for requests expiring today with no existing notification."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)

        self.assertTrue(
            should_notify_past_expiration(request.submitter, request)
        )

    def test_true_if_expires_before_today(self) -> None:
        """Verify returns `True` for requests expiring yesterday with no existing notification."""

        request = AllocationRequestFactory(expire=date.today() - timedelta(days=1))
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)

        self.assertTrue(
            should_notify_past_expiration(request.submitter, request)
        )

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_notification_filter: Mock) -> None:
        """Verify returns `False` if a notification has already been issued."""

        mock_notification_filter.return_value.exists.return_value = True

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)

        self.assertFalse(
            should_notify_past_expiration(request.submitter, request)
        )

    def test_false_if_disabled_in_preferences(self) -> None:
        """Verify returns `False` if expiry notifications are disabled in user preferences."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=False)

        self.assertFalse(
            should_notify_past_expiration(request.submitter, request)
        )

    def test_false_if_expires_after_today(self) -> None:
        """Verify returns `False` when the request has not yet expired."""

        request = AllocationRequestFactory(expire=date.today() + timedelta(days=1))
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)

        self.assertFalse(
            should_notify_past_expiration(request.submitter, request)
        )
