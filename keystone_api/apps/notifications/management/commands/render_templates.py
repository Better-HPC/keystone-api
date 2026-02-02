"""A Django management command for rendering a local copy of user notification templates.

## Arguments

| Argument    | Description                                                      |
|-------------|------------------------------------------------------------------|
| --out       | The output directory where rendered templates are written.       |
| --templates | An optional directory of custom HTML templates to render.        |
"""

from argparse import ArgumentParser
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.test import override_settings

from apps.notifications.factories import NotificationFactory
from apps.notifications.models import Notification


class Command(BaseCommand):
    """Render user notification templates and save examples to disk."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments to the parser.

        Args:
            parser: The argument parser instance.
        """

        parser.add_argument('--out',
            type=Path,
            default=Path.cwd(),
            help='The output directory where rendered templates are written.')

        parser.add_argument('--templates',
            type=Path,
            default=settings.EMAIL_TEMPLATE_DIR,
            help='An optional directory of custom HTML templates to render.')

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        input_dir = options['templates']
        output_dir = options['out']

        # Ensure in/out directories exist
        for path in (input_dir, output_dir):
            if not path.exists():
                self.stderr.write(f'No such file or directory: {path.resolve()}')
                exit(1)

        # Write example notifications to disk
        with override_settings(EMAIL_TEMPLATE_DIR=input_dir):
            self._render_notification(Notification.NotificationType.request_expiring, output_dir, "upcoming_expiration.eml")
            self._render_notification(Notification.NotificationType.request_expired, output_dir, "past_expiration.eml")
            self._render_notification(Notification.NotificationType.general_message, output_dir, "general_message.eml")

        self.stdout.write(self.style.SUCCESS(f'Templates written to {output_dir.resolve()}'))

    @staticmethod
    def _render_notification(notification_type: Notification.NotificationType, output_dir: Path, filename: str) -> None:
        """Render a sample notification and write it to disk.

        Args:
            output_dir: The directory to write the rendered email file.
            notification_type: The type of notification to render.
            filename: The output filename for the rendered email.
        """

        notification = NotificationFactory.build(notification_type=notification_type)

        mail = EmailMultiAlternatives(
            notification.subject,
            notification.message_text,
            settings.EMAIL_FROM_ADDRESS
        )

        mail.attach_alternative(notification.message_html, "text/html")
        with output_dir.joinpath(filename).open(mode="w") as f:
            f.write(mail.message().as_string())
