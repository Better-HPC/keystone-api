"""A Django management command for rendering a local copy of user notification templates.

## Arguments

| Argument    | Description                                                      |
|-------------|------------------------------------------------------------------|
| --out       | The output directory where rendered templates are written.       |
| --templates | An optional directory of custom HTML templates to render.        |
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
    _email_backend = 'plugins.email.EmlFileEmailBackend'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments to the parser.

        Args:
            parser: The argument parser instance.
        """

        parser.add_argument('--out',
            type=Path,
            help='The output directory where rendered templates are written.')

        parser.add_argument('--templates',
            type=Path,
            default=Path.cwd(),
            help='An optional directory of custom HTML templates to render.')

    def handle(self, *args, **options):
        """Handle the command execution."""

        output_dir, input_dir = self._validate_args(*args, **options)

        try:
            self._render_templates(output_dir, input_dir)

        except Exception as e:
            self.stderr.write(str(e))

    def _validate_args(self, *args, **options) -> (Path, Path | None):
        """Validate and return command line arguments.

        Returns:
            A tuple containing the input and directories.
        """

        output_dir = options['out']
        input_dir = options['templates']

        for path in (input_dir, output_dir):
            if not path.exists():
                self.stderr.write(f'No such file or directory: {path.resolve()}')
                exit(1)

        return output_dir, input_dir

    def _render_templates(self, output_dir: Path, input_dir: Path | None) -> None:
        """Render a copy of user notification templates and write them to disk.

        Args:
            output_dir: The output directory where rendered templates are written.
            input_dir: Optional input directory with custom templates.
        """

        # Define mock data to populate notifications
        user = self._create_dummy_user()
        alloc_request = self._create_dummy_allocation_request()

        # Override settings so notifications are written to disk
        with override_settings(
            EMAIL_BACKEND=self._email_backend,
            EMAIL_FILE_PATH=output_dir,
            EMAIL_TEMPLATE_DIR=input_dir
        ):
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
