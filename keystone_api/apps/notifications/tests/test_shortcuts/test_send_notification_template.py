"""Unit tests for the `send_notification_template` function."""

import jinja2
from django.core import mail
from django.template.exceptions import TemplateDoesNotExist
from django.test import override_settings, TestCase

from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification_template
from apps.users.models import User
from main import settings


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendNotificationTemplateMethod(TestCase):
    """Test sending email templates via the `send_notification_template` function."""

    def setUp(self) -> None:
        """Send an email template to a dummy user."""

        self.user = User.objects.create_user(
            email='test@example.com',
            username='foobar',
            first_name='Foo',
            last_name='Bar',
            password='foobar123'
        )

    def test_email_content(self) -> None:
        """Verify the email notification is sent with the correct content."""

        subject = 'Test subject'

        send_notification_template(
            self.user,
            subject,
            template='general.html',
            context={"user": self.user, "message": "this is a message"},
            notification_type=Notification.NotificationType.general_message
        )

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(subject, email.subject)
        self.assertEqual(settings.EMAIL_FROM_ADDRESS, email.from_email)
        self.assertEqual([self.user.email], email.to)

    def test_database_is_updated(self) -> None:
        """Verify a record of the email is stored in the database."""

        notification_type = Notification.NotificationType.general_message
        notification_metadata = {'key': 'value'}

        send_notification_template(
            self.user,
            "Test subject",
            template='general.html',
            context={"user": self.user, "message": "this is a message"},
            notification_type=notification_type,
            notification_metadata=notification_metadata
        )

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification_type, notification.notification_type)
        self.assertEqual(notification_metadata, notification.metadata)

    def test_missing_template(self) -> None:
        """Verify an error is raised when a template is not found."""

        with self.assertRaises(TemplateDoesNotExist):
            send_notification_template(
                self.user,
                "Test subject",
                template='this_template_does_not_exist',
                context=dict(),
                notification_type=Notification.NotificationType.general_message
            )

    def test_incomplete_rendering(self) -> None:
        """Verify an error is raised when a template isn't completely rendered."""

        with self.assertRaises(jinja2.UndefinedError):
            send_notification_template(
                self.user,
                "Test subject",
                template='general.html',
                context=dict(),
                notification_type=Notification.NotificationType.general_message
            )
