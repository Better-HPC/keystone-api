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

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import override_settings

from apps.allocations.factories import AllocationFactory, AllocationRequestFactory
from apps.allocations.models import AllocationRequest
from apps.notifications.tasks import send_past_expiration_notice, send_upcoming_expiration_notice


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
            default=Path.cwd(),
            help='The output directory where rendered templates are written.')

        parser.add_argument('--templates',
            type=Path,
            default=settings.EMAIL_DEFAULT_DIR,
            help='An optional directory of custom HTML templates to render.')

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        input_dir, output_dir = self._validate_args(*args, **options)

        try:
            self._render_templates(input_dir, output_dir)

        except Exception as e:
            self.stderr.write(str(e))

    def _validate_args(self, *args, **options) -> (Path, Path):
        """Validate and return command line arguments.

        Returns:
            A tuple containing the input and directories.
        """

        input_dir = options['templates']
        output_dir = options['out']

        for path in (input_dir, output_dir):
            if not path.exists():
                self.stderr.write(f'No such file or directory: {path.resolve()}')
                exit(1)

        return input_dir, output_dir

    def _render_templates(self, input_dir: Path, output_dir: Path) -> None:
        """Render a copy of user notification templates and write them to disk.

        Args:
            input_dir: Optional input directory with custom templates.
            output_dir: The output directory where rendered templates are written.
        """

        # Override settings so notifications are written to disk
        with override_settings(
            EMAIL_BACKEND=self._email_backend,
            EMAIL_FILE_PATH=output_dir,
            EMAIL_TEMPLATE_DIR=input_dir
        ):
            self._render_upcoming_expiration()
            self._render_past_expiration()

        self.stdout.write(self.style.SUCCESS(f'Templates written to {output_dir.resolve()}'))

    def _render_upcoming_expiration(self) -> None:
        """Render a sample notification for an allocation request with an upcoming expiration."""

        next_week = date.today() + timedelta(days=7)
        last_year = next_week - timedelta(days=365)
        alloc_request = AllocationRequestFactory.build(
            id=123,
            active=last_year,
            expire=next_week,
            status=AllocationRequest.StatusChoices.APPROVED
        )

        allocations = AllocationFactory.build_batch(3, request=alloc_request)

        send_upcoming_expiration_notice(
            user=alloc_request.submitter,
            request=alloc_request,
            allocations=allocations,
            save=False)

    def _render_past_expiration(self) -> None:
        """Render a sample notification for an allocation request that has expired."""

        today = date.today()
        last_year = today - timedelta(days=365)
        alloc_request = AllocationRequestFactory.build(
            id=123,
            active=last_year,
            expire=today,
            status=AllocationRequest.StatusChoices.APPROVED
        )

        allocations = AllocationFactory.build_batch(3, request=alloc_request)

        send_past_expiration_notice(
            user=alloc_request.submitter,
            request=alloc_request,
            allocations=allocations,
            save=False)
