"""Unit tests for the `send_upcoming_expiration_notice` function."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.factories import PreferenceFactory
from apps.notifications.shortcuts import format_template, get_template
from apps.notifications.tasks.upcoming_expirations import send_upcoming_expiration_notice
from apps.users.factories import UserFactory


@patch("apps.notifications.tasks.upcoming_expirations.send_notification_template")
class SendUpcomingExpirationNoticeMethod(TestCase):
    """Test the sending of "upcoming expiration" notifications."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        self.request = AllocationRequestFactory(
            submitter=self.user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=5),
        )

    def test_renders_default_template(self, mock_send: Mock) -> None:
        """Verify the task renders the default template without undefined variable errors."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs["context"]
        template = get_template("upcoming_expiration.html")
        html, text = format_template(template, context)
        self.assertTrue(html)
        self.assertTrue(text)

    def test_context_user_fields_match_user(self, mock_send: None) -> None:
        """Verify user-related context values match the notified user."""

        user = UserFactory(
            username="asmith",
            first_name="Alice",
            last_name="Smith",
            date_joined=timezone.now() - timedelta(days=365),
        )
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=5),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(user.id, request.id)

        context = mock_send.call_args.kwargs["context"]
        self.assertEqual(context["user_name"], "asmith")
        self.assertEqual(context["user_first"], "Alice")
        self.assertEqual(context["user_last"], "Smith")

    def test_context_request_fields_match_request(self, mock_send: None) -> None:
        """Verify request-related context values match the expiring allocation request."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs["context"]
        self.assertEqual(context["req_id"], self.request.id)
        self.assertEqual(context["req_title"], self.request.title)
        self.assertEqual(context["req_team"], self.request.team.name)
        self.assertEqual(context["req_submitted"], self.request.submitted)
        self.assertEqual(context["req_active"], self.request.active)
        self.assertEqual(context["req_expire"], self.request.expire)

    def test_context_days_left_is_correct(self, mock_send: None) -> None:
        """Verify the days remaining until expiration is calculated correctly."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs["context"]
        self.assertEqual(context["req_days_left"], 5)

    def test_context_allocations_are_populated(self, mock_send: None) -> None:
        """Verify the allocations list is a non-empty tuple with expected keys."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs["context"]
        self.assertIsInstance(context["allocations"], tuple)
        for alloc in context["allocations"]:
            self.assertIn("alloc_cluster", alloc)
            self.assertIn("alloc_requested", alloc)
            self.assertIn("alloc_awarded", alloc)

    def test_context_upcoming_requests_have_expected_keys(self, mock_send: None) -> None:
        """Verify upcoming request entries contain the expected keys."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs["context"]
        self.assertIsInstance(context["upcoming_requests"], tuple)
        for req in context["upcoming_requests"]:
            self.assertIn("id", req)
            self.assertIn("title", req)
            self.assertIn("submitted", req)
            self.assertIn("active", req)
            self.assertIn("expire", req)
            self.assertIn("status", req)

    def test_notification_metadata_includes_request_id_and_days(self, mock_send: None) -> None:
        """Verify the notification metadata includes the request ID and days to expiration."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        metadata = mock_send.call_args.kwargs["notification_metadata"]
        self.assertEqual(metadata["request_id"], self.request.id)
        self.assertEqual(metadata["days_to_expire"], 5)

    def test_subject_includes_request_id(self, mock_send: None) -> None:
        """Verify the email subject line includes the allocation request ID."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        subject = mock_send.call_args.kwargs["subject"]
        self.assertIn(str(self.request.id), subject)

    @patch("apps.notifications.tasks.past_expirations.should_notify_past_expiration")
    def test_not_sent_when_should_notify_is_false(self, mock_should_notify: Mock, mock_send: Mock) -> None:
        """Verify the notification is not sent when the user should not be notified."""

        mock_should_notify.return_value = False

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        preference = PreferenceFactory(user=user, request_expiry_thresholds=[5])
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=15),
        )

        send_upcoming_expiration_notice(user.id, request.id)
        mock_send.assert_not_called()
