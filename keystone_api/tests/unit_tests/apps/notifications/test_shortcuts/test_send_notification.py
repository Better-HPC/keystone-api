"""Unit tests for the `send_notification` function."""

from django.conf import settings
from django.core import mail
from django.db import IntegrityError
from django.test import override_settings, TestCase

from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification
from apps.notifications.utils import sanitize_html
from apps.users.factories import UserFactory

SUBJECT = "Test Subject"
HTML_TEXT = "<p>This is an <b>HTML</b> message.</p>"
PLAIN_TEXT = sanitize_html(HTML_TEXT)
NOTIFICATION_METADATA = {"key": "value"}
NOTIFICATION_TYPE = Notification.NotificationType.general_message


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendNotificationMethod(TestCase):
    """Test sending emails via the `send_notification` function."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory(
            email="test@example.com",
            username="foobar",
            first_name="Foo",
            last_name="Bar",
            password="foobar123",
        )

    def test_email_content(self) -> None:
        """Verify an email notification is sent with the correct content."""

        send_notification(self.user, SUBJECT, PLAIN_TEXT, HTML_TEXT, NOTIFICATION_TYPE, NOTIFICATION_METADATA)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(SUBJECT, email.subject)
        self.assertEqual(PLAIN_TEXT, email.body)
        self.assertEqual(settings.EMAIL_FROM_ADDRESS, email.from_email)
        self.assertEqual([self.user.email], email.to)
        self.assertEqual([(HTML_TEXT, "text/html")], email.alternatives)

    def test_saved_to_database(self) -> None:
        """Verify a record of the email is stored in the database."""

        send_notification(self.user, SUBJECT, PLAIN_TEXT, HTML_TEXT, NOTIFICATION_TYPE, NOTIFICATION_METADATA)

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(PLAIN_TEXT, notification.message_text)
        self.assertEqual(HTML_TEXT, notification.message_html)
        self.assertEqual(NOTIFICATION_TYPE, notification.notification_type)
        self.assertEqual(NOTIFICATION_METADATA, notification.metadata)

    def test_metadata_defaults_to_none(self) -> None:
        """Verify the database record has null metadata when `notification_metadata` is omitted."""

        send_notification(self.user, SUBJECT, PLAIN_TEXT, HTML_TEXT, NOTIFICATION_TYPE)

        notification = Notification.objects.get(user=self.user)
        self.assertIsNone(notification.metadata)

    def test_duplicate_raises_integrity_error(self) -> None:
        """Verify a duplicate notification raises an error before dispatching a second email."""

        send_notification(self.user, SUBJECT, PLAIN_TEXT, HTML_TEXT, NOTIFICATION_TYPE, NOTIFICATION_METADATA)
        self.assertEqual(len(mail.outbox), 1)

        # Second call with identical user, type, and metadata must raise before sending
        with self.assertRaises(IntegrityError):
            send_notification(self.user, SUBJECT, PLAIN_TEXT, HTML_TEXT, NOTIFICATION_TYPE, NOTIFICATION_METADATA)

        self.assertEqual(len(mail.outbox), 1, "No second email should have been dispatched")
