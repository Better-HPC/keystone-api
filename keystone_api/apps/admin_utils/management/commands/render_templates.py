"""A Django management command for rendering a local copy of user notification templates.

## Arguments

| Argument    | Description                                                      |
|-------------|------------------------------------------------------------------|
| --templates | The directory of HTML templates to render.                       |
| --out       | The output directory to write templates to.                      |
"""

from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.test import override_settings

from apps.allocations.models import AllocationRequest
from apps.allocations.shortcuts import send_notification_past_expiration, send_notification_upcoming_expiration
from apps.users.models import User


class Command(BaseCommand):
    """Render user notification templates and save examples to disk."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments to the parser.

        Args:
            parser: The argument parser instance.
        """

        parser.add_argument('--templates', type=Path, help='The directory of HTML templates to render.')
        parser.add_argument('--out', type=Path, help='The output directory to write templates to.')

    def handle(self, *args, **options):
        """Handle the command execution."""

        # Define custom SMTP/notification settings
        output_dir = options['out']
        input_dir = options['templates']
        backend = 'plugins.email.EmlFileBasedEmailBackend'

        # Define mock data to populate notifications
        user = self._create_dummy_user()
        alloc_request = self._create_dummy_allocation_request()

        # Override settings so notifications are written to disk
        with override_settings(EMAIL_BACKEND=backend, EMAIL_FILE_PATH=output_dir, EMAIL_TEMPLATE_DIR=input_dir):
            send_notification_upcoming_expiration(user=user, request=alloc_request, save=False)
            send_notification_past_expiration(user=user, request=alloc_request, save=False)

        self.stdout.write(self.style.SUCCESS(f'Templates written to {output_dir.resolve()}'))

    @staticmethod
    def _create_dummy_user() -> User:
        """Create a `User` object suitable for use when formatting example notification templates."""

        return User(
            username="username",
            first_name="first_name",
            last_name="last_name",
            email="username.email.com"
        )

    @staticmethod
    def _create_dummy_allocation_request() -> AllocationRequest:
        """Create an `AllocationRequest` object suitable for use when formatting example notification templates."""

        return AllocationRequest(
            title="Allocation Request Title",
            description="This is a project description.",
            submitted=date.today() - timedelta(days=370),
            active=date.today() - timedelta(days=365),
            expire=date.today(),
            status=AllocationRequest.StatusChoices.APPROVED,
        )
