"""Unit tests for the `send_notification_template` function."""

import tempfile
from pathlib import Path

import jinja2
from django.core import mail
from django.db import IntegrityError
from django.test import override_settings, TestCase

from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification_template
from apps.users.factories import UserFactory
from main import settings

SUBJECT = "Test Subject"
NOTIFICATION_TYPE = Notification.NotificationType.general_message
NOTIFICATION_METADATA = {"request_id": 42}
GENERAL_CONTEXT = {
    "user_first": "Foo",
    "user_last": "Bar",
    "user_name": "foobar",
    "message": "this is a message",
}


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendNotificationTemplateMethod(TestCase):
    """Test sending email templates via the `send_notification_template` function."""

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
        """Verify the email notification is sent with the correct content."""

        send_notification_template(
            self.user,
            SUBJECT,
            template="general.html",
            context=GENERAL_CONTEXT,
            notification_type=NOTIFICATION_TYPE,
        )

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(SUBJECT, email.subject)
        self.assertEqual(settings.EMAIL_FROM_ADDRESS, email.from_email)
        self.assertEqual([self.user.email], email.to)

    def test_database_is_updated(self) -> None:
        """Verify a record of the email is stored in the database."""

        send_notification_template(
            self.user,
            SUBJECT,
            template="general.html",
            context=GENERAL_CONTEXT,
            notification_type=NOTIFICATION_TYPE,
            notification_metadata=NOTIFICATION_METADATA,
        )

        notification = Notification.objects.get(user=self.user)
        self.assertEqual(NOTIFICATION_TYPE, notification.notification_type)
        self.assertEqual(NOTIFICATION_METADATA, notification.metadata)

    def test_missing_template(self) -> None:
        """Verify an error is raised when a template is not found."""

        with self.assertRaises(FileNotFoundError):
            send_notification_template(
                self.user,
                SUBJECT,
                template="this_template_does_not_exist",
                context=dict(),
                notification_type=NOTIFICATION_TYPE,
            )

    def test_incomplete_rendering(self) -> None:
        """Verify an error is raised when a template isn't completely rendered."""

        with self.assertRaises(jinja2.UndefinedError):
            send_notification_template(
                self.user,
                SUBJECT,
                template="general.html",
                context=dict(),
                notification_type=NOTIFICATION_TYPE,
            )

    def test_world_writable_template_raises_permission_error(self) -> None:
        """Verify an error is raised when the template file has insecure permissions."""

        with tempfile.TemporaryDirectory() as template_dir:
            template_path = Path(template_dir) / "general.html"
            template_path.write_text("<p>{{ message }}</p>")
            template_path.chmod(0o446)

            with (
                override_settings(EMAIL_TEMPLATE_DIR=Path(template_dir)),
                self.assertRaisesRegex(PermissionError, "insecure file permissions"),
            ):
                send_notification_template(
                    self.user,
                    SUBJECT,
                    template="general.html",
                    context=GENERAL_CONTEXT,
                    notification_type=NOTIFICATION_TYPE,
                )

    def test_duplicate_raises_integrity_error(self) -> None:
        """Verify a duplicate notification raises an error before dispatching a second email."""

        kwargs = dict(
            template="general.html",
            context=GENERAL_CONTEXT,
            notification_type=NOTIFICATION_TYPE,
            notification_metadata=NOTIFICATION_METADATA,
        )

        send_notification_template(self.user, SUBJECT, **kwargs)
        self.assertEqual(len(mail.outbox), 1)

        # Second identical call must raise before sending another email
        with self.assertRaises(IntegrityError):
            send_notification_template(self.user, SUBJECT, **kwargs)

        self.assertEqual(len(mail.outbox), 1, "No second email should have been dispatched")
