"""Unit tests for the `send_notification` function."""

from django.conf import settings
from django.core import mail
from django.test import override_settings, TestCase

from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification
from apps.users.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendNotificationMethod(TestCase):
    """Test sending emails via the `send_notification` function"""

    def setUp(self) -> None:
        """Send an email notification to a dummy user"""

        self.user = User.objects.create_user(
            email='test@example.com',
            username='foobar',
            first_name='Foo',
            last_name='Bar',
            password='foobar123'
        )

        self.subject = 'Test Subject'
        self.plain_text = 'This is a plain text message.'
        self.html_text = '<p>This is an HTML message.</p>'
        self.notification_type = Notification.NotificationType.general_message
        self.notification_metadata = {'key': 'value'}

        send_notification(
            self.user,
            self.subject,
            self.plain_text,
            self.html_text,
            self.notification_type,
            self.notification_metadata)

    def test_email_content(self) -> None:
        """Verify an email notification is sent with the correct content"""

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(self.subject, email.subject)
        self.assertEqual(self.plain_text, email.body)
        self.assertEqual(settings.EMAIL_FROM_ADDRESS, email.from_email)
        self.assertEqual([self.user.email], email.to)
        self.assertEqual([(self.html_text, 'text/html')], email.alternatives)

    def test_database_is_updated(self) -> None:
        """Verify a record of the email is stored in the database"""

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(self.plain_text, notification.message)
        self.assertEqual(self.notification_type, notification.notification_type)
        self.assertEqual(self.notification_metadata, notification.metadata)
