"""Tests for the `tasks.upcoming_expirations` module."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.factories import PreferenceFactory
from apps.notifications.shortcuts import format_template, get_template
from apps.notifications.tasks.upcoming_expirations import send_upcoming_expiration_notice, should_notify_upcoming_expiration
from apps.users.factories import UserFactory


class ShouldNotifyUpcomingExpirationMethod(TestCase):
    """Test the determination of whether a notification should be issued for an upcoming expiration."""

    def test_true_if_new_notification(self) -> None:
        """Verify returns `True` if a notification threshold has been hit."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=5),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[5])
        self.assertTrue(
            should_notify_upcoming_expiration(user, request)
        )

    @patch('apps.notifications.models.Notification.objects.filter')
    def test_false_if_duplicate_notification(self, mock_filter: Mock) -> None:
        """Verify returns `False` if a notification has already been issued."""

        # Simulate an existing notification in DB
        mock_filter.return_value.exists.return_value = True

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=20),
            active=date.today() - timedelta(days=20),
            expire=date.today() + timedelta(days=15),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_does_not_expire(self) -> None:
        """Verify returns `False` if the request does not expire."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=10),
            active=date.today() - timedelta(days=10),
            expire=None,
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_already_expired(self) -> None:
        """Verify returns `False` if the request has already expired."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=20),
            active=date.today() - timedelta(days=20),
            expire=date.today(),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_no_threshold_reached(self) -> None:
        """Verify returns `False` if no threshold has been reached."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=20),
            active=date.today() - timedelta(days=20),
            expire=date.today() + timedelta(days=15),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[5])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_user_recently_joined(self) -> None:
        """Verify returns `False` if the user is new."""

        user = UserFactory(date_joined=timezone.now())
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now(),
            active=date.today(),
            expire=date.today() + timedelta(days=15),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )

    def test_false_if_request_recently_activated(self) -> None:
        """Verify returns `False` if the active date is after the notification threshold."""

        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=10),
            active=date.today(),
            expire=date.today() + timedelta(days=10),
        )

        PreferenceFactory(user=user, request_expiry_thresholds=[15])
        self.assertFalse(
            should_notify_upcoming_expiration(user, request)
        )


@patch('apps.notifications.tasks.upcoming_expirations.send_notification_template')
class SendUpcomingExpirationNoticeContext(TestCase):
    """Test the template context passed by the upcoming expiration notification task."""

    def setUp(self) -> None:
        self.user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        self.request = AllocationRequestFactory(
            submitter=self.user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=5),
        )

    def test_context_renders_default_template(self, mock_send: Mock) -> None:
        """Verify the task context renders the default template without undefined variable errors."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs['context']
        template = get_template('upcoming_expiration.html')
        html, text = format_template(template, context)
        self.assertTrue(html)
        self.assertTrue(text)

    def test_context_user_fields_match_user(self, mock_send: None) -> None:
        """Verify user-related context values match the notified user."""

        user = UserFactory(
            username='asmith',
            first_name='Alice',
            last_name='Smith',
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

        context = mock_send.call_args.kwargs['context']
        self.assertEqual(context['user_name'], 'asmith')
        self.assertEqual(context['user_first'], 'Alice')
        self.assertEqual(context['user_last'], 'Smith')

    def test_context_request_fields_match_request(self, mock_send: None) -> None:
        """Verify request-related context values match the expiring allocation request."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertEqual(context['req_id'], self.request.id)
        self.assertEqual(context['req_title'], self.request.title)
        self.assertEqual(context['req_team'], self.request.team.name)
        self.assertEqual(context['req_submitted'], self.request.submitted)
        self.assertEqual(context['req_active'], self.request.active)
        self.assertEqual(context['req_expire'], self.request.expire)

    def test_context_days_left_is_correct(self, mock_send: None) -> None:
        """Verify the days remaining until expiration is calculated correctly."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertEqual(context['req_days_left'], 5)

    def test_context_allocations_are_populated(self, mock_send: None) -> None:
        """Verify the allocations list is a non-empty tuple with expected keys."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertIsInstance(context['allocations'], tuple)
        for alloc in context['allocations']:
            self.assertIn('alloc_cluster', alloc)
            self.assertIn('alloc_requested', alloc)
            self.assertIn('alloc_awarded', alloc)

    def test_context_upcoming_requests_have_expected_keys(self, mock_send: None) -> None:
        """Verify upcoming request entries contain the expected keys."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertIsInstance(context['upcoming_requests'], tuple)
        for req in context['upcoming_requests']:
            self.assertIn('id', req)
            self.assertIn('title', req)
            self.assertIn('submitted', req)
            self.assertIn('active', req)
            self.assertIn('expire', req)
            self.assertIn('status', req)

    def test_notification_metadata_includes_request_id_and_days(self, mock_send: None) -> None:
        """Verify the notification metadata includes the request ID and days to expiration."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        metadata = mock_send.call_args.kwargs['notification_metadata']
        self.assertEqual(metadata['request_id'], self.request.id)
        self.assertEqual(metadata['days_to_expire'], 5)

    def test_subject_includes_request_id(self, mock_send: None) -> None:
        """Verify the email subject line includes the allocation request ID."""

        PreferenceFactory(user=self.user, request_expiry_thresholds=[5])
        send_upcoming_expiration_notice(self.user.id, self.request.id)

        subject = mock_send.call_args.kwargs['subject']
        self.assertIn(str(self.request.id), subject)

    def test_not_called_when_should_notify_is_false(self, mock_send: None) -> None:
        """Verify the notification is not sent when the user should not be notified."""

        # Create an allocation request that does not expire within the notification threshold
        user = UserFactory(date_joined=timezone.now() - timedelta(days=365))
        PreferenceFactory(user=user, request_expiry_thresholds=[5])

        request = AllocationRequestFactory(
            submitter=user,
            submitted=timezone.now() - timedelta(days=30),
            active=date.today() - timedelta(days=30),
            expire=date.today() + timedelta(days=15),
        )

        send_upcoming_expiration_notice(user.id, request.id)
        mock_send.assert_not_called()
