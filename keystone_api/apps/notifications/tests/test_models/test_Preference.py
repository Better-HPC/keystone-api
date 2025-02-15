"""Unit tests for the `Preference` class."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import default_expiry_thresholds, Preference

User = get_user_model()


class GetUserPreferenceMethod(TestCase):
    """Tests for getting user preferences."""

    def setUp(self) -> None:
        """Create a test user."""

        self.user = User.objects.create_user(username='testuser', password='foobar123!')

    def test_get_user_preference_creates_new_preference(self) -> None:
        """Method a new Preference object is created if one does not exist."""

        # Test a record is created
        self.assertFalse(Preference.objects.filter(user=self.user).exists())
        preference = Preference.get_user_preference(user=self.user)
        self.assertTrue(Preference.objects.filter(user=self.user).exists())

        # Ensure preference is created with appropriate defaults
        self.assertEqual(self.user, preference.user)
        self.assertListEqual(default_expiry_thresholds(), preference.request_expiry_thresholds)

    def test_get_user_preference_returns_existing_preference(self) -> None:
        """Method an existing Preference object is returned if it already exists."""

        existing_preference = Preference.objects.create(user=self.user)
        preference = Preference.get_user_preference(user=self.user)
        self.assertEqual(existing_preference, preference)


class SetUserPreferenceMethod(TestCase):
    """Tests for setting user preferences."""

    def setUp(self) -> None:
        """Create a test user."""

        self.user = User.objects.create_user(username='testuser', password='foobar123!')

    def test_set_user_preference_creates_preference(self) -> None:
        """Method a new Preference object is created with specified values."""

        self.assertFalse(Preference.objects.filter(user=self.user).exists())

        Preference.set_user_preference(user=self.user, notify_on_expiration=False)
        preference = Preference.objects.get(user=self.user)
        self.assertFalse(preference.notify_on_expiration)

    def test_set_user_preference_updates_existing_preference(self) -> None:
        """Method an existing Preference object is updated with specified values."""

        preference = Preference.objects.create(user=self.user, notify_on_expiration=True)
        self.assertTrue(Preference.objects.filter(user=self.user).exists())

        Preference.set_user_preference(user=self.user, notify_on_expiration=False)
        preference.refresh_from_db()
        self.assertFalse(preference.notify_on_expiration)


class GetNextExpirationThreshold(TestCase):
    """Test determining the next threshold for an expiry notification."""

    def setUp(self) -> None:
        """Set up test data."""

        self.user = get_user_model().objects.create_user(username="testuser", password="foobar123")
        self.preference = Preference.objects.create(
            user=self.user,
            request_expiry_thresholds=[7, 14, 30]
        )

    def test_get_next_expiration_threshold_with_valid_threshold(self) -> None:
        """Test with a valid threshold available."""

        next_threshold = self.preference.get_next_expiration_threshold(10)
        self.assertEqual(next_threshold, 14)

    def test_get_next_expiration_threshold_with_exact_match(self) -> None:
        """Test with an exact match to the threshold."""

        next_threshold = self.preference.get_next_expiration_threshold(14)
        self.assertEqual(next_threshold, 14)

    def test_get_next_expiration_threshold_with_no_valid_threshold(self) -> None:
        """Test when no valid threshold is available."""

        next_threshold = self.preference.get_next_expiration_threshold(31)
        self.assertIsNone(next_threshold)

    def test_get_next_expiration_threshold_with_empty_threshold_list(self) -> None:
        """Test with an empty list of thresholds."""

        self.preference.request_expiry_thresholds = []
        next_threshold = self.preference.get_next_expiration_threshold(10)
        self.assertIsNone(next_threshold)

    def test_get_next_expiration_threshold_with_all_lower_thresholds(self) -> None:
        """Test when all thresholds are lower than the given days."""

        next_threshold = self.preference.get_next_expiration_threshold(1)
        self.assertEqual(next_threshold, 7)
