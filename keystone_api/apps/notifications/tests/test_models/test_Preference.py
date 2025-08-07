"""Unit tests for the `Preference` class."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.models import default_expiry_thresholds, Preference
from apps.users.factories import UserFactory

User = get_user_model()


class GetExpirationThresholdMethod(TestCase):
    """Test determining the next expiry notification threshold via the `get_expiration_threshold` method."""

    def setUp(self) -> None:
        """Set up test data."""

        self.user = get_user_model().objects.create_user(username="testuser", password="foobar123")
        self.preference = Preference.objects.create(
            user=self.user,
            request_expiry_thresholds=[7, 14, 30]
        )

    def test_value_below_thresholds(self) -> None:
        """Verify the calculation when the given value is below all thresholds."""

        next_threshold = self.preference.get_expiration_threshold(1)
        self.assertEqual(next_threshold, 7)

    def test_value_between_thresholds(self) -> None:
        """Verify the calculation when the given value is between two valid thresholds."""

        next_threshold = self.preference.get_expiration_threshold(10)
        self.assertEqual(next_threshold, 14)

    def test_value_above_thresholds(self) -> None:
        """Verify `None` is returned when the given value is above all thresholds."""

        next_threshold = self.preference.get_expiration_threshold(31)
        self.assertIsNone(next_threshold)

    def test_with_exact_match(self) -> None:
        """Verify the calculation when the given value matches a threshold exactly."""

        next_threshold = self.preference.get_expiration_threshold(14)
        self.assertEqual(next_threshold, 14)

    def test_empty_threshold_list(self) -> None:
        """Verify `None` is returned for empty list of thresholds."""

        self.preference.request_expiry_thresholds = []
        next_threshold = self.preference.get_expiration_threshold(10)
        self.assertIsNone(next_threshold)


class GetUsageThresholdMethod(TestCase):
    """Test determining the next usage notification threshold via the `get_usage_threshold` method."""

    def setUp(self) -> None:
        """Set up test data."""

        self.user = get_user_model().objects.create_user(username="testuser", password="foobar123")
        self.preference = Preference.objects.create(
            user=self.user,
            request_expiry_thresholds=[10, 20, 30, 50, 75]
        )

    def test_value_below_all_thresholds(self) -> None:
        """Verify the calculation when the given value is below all thresholds."""

        next_threshold = self.preference.get_usage_threshold(5)
        self.assertEqual(next_threshold, None)

    def test_value_between_thresholds(self) -> None:
        """Verify the calculation when the given value is between two valid thresholds."""

        next_threshold = self.preference.get_usage_threshold(25)
        self.assertEqual(next_threshold, 20)

    def test_value_above_all_thresholds(self) -> None:
        """Verify the calculation when the given value is above all thresholds."""

        next_threshold = self.preference.get_usage_threshold(80)
        self.assertEqual(next_threshold, 75)

    def test_value_exact_match(self) -> None:
        """Verify the calculation when the given value exactly matches a threshold."""

        next_threshold = self.preference.get_usage_threshold(50)
        self.assertEqual(next_threshold, 50)

    def test_empty_threshold_list(self) -> None:
        """Verify `None` is returned for empty list of thresholds."""

        self.preference.request_expiry_thresholds = []
        next_threshold = self.preference.get_usage_threshold(10)
        self.assertIsNone(next_threshold)


class GetUserPreferenceMethod(TestCase):
    """Test getting user preferences via the `get_user_preference` method."""

    def setUp(self) -> None:
        """Create a test user."""

        self.user = User.objects.create_user(username='testuser', password='foobar123!')

    def test_get_user_preference_creates_new_preference(self) -> None:
        """Verify a new Preference object is created if one does not exist."""

        # Test a record is created
        self.assertFalse(Preference.objects.filter(user=self.user).exists())
        preference = Preference.get_user_preference(user=self.user)
        self.assertTrue(Preference.objects.filter(user=self.user).exists())

        # Ensure preference is created with appropriate defaults
        self.assertEqual(self.user, preference.user)
        self.assertListEqual(default_expiry_thresholds(), preference.request_expiry_thresholds)

    def test_get_user_preference_returns_existing_preference(self) -> None:
        """Verify an existing Preference object is returned if it already exists."""

        existing_preference = Preference.objects.create(user=self.user)
        preference = Preference.get_user_preference(user=self.user)
        self.assertEqual(existing_preference, preference)


class SetUserPreferenceMethod(TestCase):
    """Test setting user preferences via the `set_user_preference` method."""

    def setUp(self) -> None:
        """Create a test user."""

        self.user = User.objects.create_user(username='testuser', password='foobar123!')

    def test_set_user_preference_creates_preference(self) -> None:
        """Verify a new Preference object is created with specified values."""

        self.assertFalse(Preference.objects.filter(user=self.user).exists())

        Preference.set_user_preference(user=self.user, notify_on_expiration=False)
        preference = Preference.objects.get(user=self.user)
        self.assertFalse(preference.notify_on_expiration)

    def test_set_user_preference_updates_existing_preference(self) -> None:
        """Verify an existing Preference object is updated with specified values."""

        preference = Preference.objects.create(user=self.user, notify_on_expiration=True)
        self.assertTrue(Preference.objects.filter(user=self.user).exists())

        Preference.set_user_preference(user=self.user, notify_on_expiration=False)
        preference.refresh_from_db()
        self.assertFalse(preference.notify_on_expiration)


class ShouldNotifyPastExpirationMethod(TestCase):
    """Test the determination of whether a notification should be issued for an expired allocation."""

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_notification_filter: Mock) -> None:
        """Verify the return value is `False` if a notification has already been issued."""

        mock_notification_filter.return_value.exists.return_value = True

        request = AllocationRequestFactory(expire=date.today())
        pref = Preference.objects.create(user=request.submitter, notify_on_expiration=True)
        self.assertFalse(pref.should_notify_past_expiration(request.id))

    def test_false_if_disabled_in_preferences(self) -> None:
        """Verify the return value is `False` if expiry notifications are disabled in preferences."""

        request = AllocationRequestFactory(expire=date.today())
        pref = Preference.objects.create(user=request.submitter, notify_on_expiration=False)
        self.assertFalse(pref.should_notify_past_expiration(request.id))

    def test_true_if_new_notification(self) -> None:
        """Verify the return value is `True` if a notification has not been issued yet."""

        request = AllocationRequestFactory(expire=date.today())
        pref = Preference.objects.create(user=request.submitter, notify_on_expiration=True)
        self.assertTrue(pref.should_notify_past_expiration(request.id))


class ShouldNotifyUpcomingExpirationMethod(TestCase):
    """Test the determination of whether a notification should be issued for an upcoming expiration."""

    def test_false_if_request_does_not_expire(self) -> None:
        """Verify the return value is `False` if the request does not expire."""

        request = AllocationRequestFactory(expire=None)
        pref = Preference.objects.create(user=request.submitter, request_expiry_thresholds=[15])
        self.assertFalse(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )

    def test_false_if_request_already_expired(self) -> None:
        """Verify the return value is `False` if the request has already expired."""

        request = AllocationRequestFactory(expire=date.today())
        pref = Preference.objects.create(user=request.submitter, request_expiry_thresholds=[15])
        self.assertFalse(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )

    def test_false_if_no_threshold_reached(self) -> None:
        """Verify the return value is `False` if no threshold has been reached."""

        request = AllocationRequestFactory(expire=date.today() + timedelta(days=15))
        pref = Preference.objects.create(user=request.submitter, request_expiry_thresholds=[5])
        self.assertFalse(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )

    def test_false_if_user_recently_joined(self) -> None:
        """Verify the return value is `False` if the user is new."""

        user = UserFactory(date_joined=datetime.now())
        request = AllocationRequestFactory(expire=date.today() + timedelta(days=15))
        pref = Preference.objects.create(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_filter: Mock) -> None:
        """Verify the return value is `False` if a notification has already been issued."""

        mock_filter.return_value.exists.return_value = True

        request = AllocationRequestFactory(expire=date.today() + timedelta(days=15))
        pref = Preference.objects.create(user=request.submitter, request_expiry_thresholds=[5])
        self.assertFalse(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )

    def test_true_if_new_notification(self) -> None:
        """Verify the return value is `True` if a notification threshold has been hit."""

        request = AllocationRequestFactory(expire=date.today() + timedelta(days=5))
        pref = Preference.objects.create(user=request.submitter, request_expiry_thresholds=[15])
        self.assertTrue(
            pref.should_notify_upcoming_expiration(request.id, request.expire)
        )
