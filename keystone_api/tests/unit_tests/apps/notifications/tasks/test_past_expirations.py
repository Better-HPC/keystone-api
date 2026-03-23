"""Tests for the `tasks.past_expirations` module."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory
from apps.notifications.factories import PreferenceFactory
from apps.notifications.shortcuts import format_template, get_template
from apps.notifications.tasks.past_expirations import send_past_expiration_notice, should_notify_past_expiration

PAST_EXPIRATION_CONTEXT_KEYS = {
    'user_name',
    'user_first',
    'user_last',
    'req_id',
    'req_title',
    'req_team',
    'req_submitted',
    'req_active',
    'req_expire',
    'allocations',
    'upcoming_requests',
}


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


@patch('apps.notifications.tasks.past_expirations.send_notification_template')
class SendPastExpirationNoticeContext(TestCase):
    """Test the template context passed by the past expiration notification task."""

    def test_context_contains_all_required_keys(self, mock_send: Mock) -> None:
        """Verify the context dictionary includes all keys expected by the template."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        mock_send.assert_called_once()
        context = mock_send.call_args.kwargs['context']
        self.assertEqual(PAST_EXPIRATION_CONTEXT_KEYS, set(context.keys()))

    def test_context_user_fields_match_user(self, mock_send: Mock) -> None:
        """Verify user-related context values match the notified user."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertEqual(context['user_name'], request.submitter.username)
        self.assertEqual(context['user_first'], request.submitter.first_name)
        self.assertEqual(context['user_last'], request.submitter.last_name)

    def test_context_request_fields_match_request(self, mock_send: Mock) -> None:
        """Verify request-related context values match the expired allocation request."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertEqual(context['req_id'], request.id)
        self.assertEqual(context['req_title'], request.title)
        self.assertEqual(context['req_team'], request.team.name)
        self.assertEqual(context['req_submitted'], request.submitted)
        self.assertEqual(context['req_active'], request.active)
        self.assertEqual(context['req_expire'], request.expire)

    def test_context_allocations_are_populated(self, mock_send: Mock) -> None:
        """Verify the allocations list is a non-empty tuple with expected keys."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertIsInstance(context['allocations'], tuple)
        for alloc in context['allocations']:
            self.assertIn('alloc_cluster', alloc)
            self.assertIn('alloc_requested', alloc)
            self.assertIn('alloc_awarded', alloc)
            self.assertIn('alloc_final', alloc)

    def test_context_upcoming_requests_have_expected_keys(self, mock_send: Mock) -> None:
        """Verify upcoming request entries contain the expected keys."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        context = mock_send.call_args.kwargs['context']
        self.assertIsInstance(context['upcoming_requests'], tuple)
        for req in context['upcoming_requests']:
            self.assertIn('id', req)
            self.assertIn('title', req)
            self.assertIn('submitted', req)
            self.assertIn('active', req)
            self.assertIn('expire', req)
            self.assertIn('status', req)

    def test_notification_metadata_includes_request_id(self, mock_send: Mock) -> None:
        """Verify the notification metadata includes the allocation request ID."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        metadata = mock_send.call_args.kwargs['notification_metadata']
        self.assertEqual(metadata['request_id'], request.id)

    def test_subject_includes_request_id(self, mock_send: Mock) -> None:
        """Verify the email subject line includes the allocation request ID."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        subject = mock_send.call_args.kwargs['subject']
        self.assertIn(str(request.id), subject)

    def test_not_called_when_should_notify_is_false(self, mock_send: Mock) -> None:
        """Verify the notification is not sent when the user should not be notified."""

        request = AllocationRequestFactory(expire=date.today() + timedelta(days=5))
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        mock_send.assert_not_called()

    def test_context_renders_default_template(self, mock_send: Mock) -> None:
        """Verify the task context renders the default template without undefined variable errors."""

        request = AllocationRequestFactory(expire=date.today())
        PreferenceFactory(user=request.submitter, notify_on_expiration=True)
        send_past_expiration_notice(request.submitter.id, request.id)

        context = mock_send.call_args.kwargs['context']
        template = get_template('past_expiration.html')
        html, text = format_template(template, context)
        self.assertTrue(html)
        self.assertTrue(text)
