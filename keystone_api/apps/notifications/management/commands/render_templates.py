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
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.test import override_settings

from apps.notifications.shortcuts import format_template, get_template


class Command(BaseCommand):
    """Render user notification templates and save examples to disk."""

    help = __doc__

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
        with override_settings(EMAIL_TEMPLATE_DIR=input_dir):
            self._render_upcoming_expiration(output_dir)
            self._render_past_expiration(output_dir)

        self.stdout.write(self.style.SUCCESS(f'Templates written to {output_dir.resolve()}'))

    def _render_templates(self, input_dir: Path, output_dir: Path) -> None:
        """Render a copy of user notification templates and write them to disk.

        Args:
            input_dir: Optional input directory with custom templates.
            output_dir: The output directory where rendered templates are written.
        """

    @staticmethod
    def _render_upcoming_expiration(output_dir: Path) -> None:
        """Render a sample notification for an allocation request with an upcoming expiration."""

        next_week = date.today() + timedelta(days=7)
        last_year = next_week - timedelta(days=365)

        template = get_template("upcoming_expiration.html")
        subject = "Your HPC allocation 1234 is expiring soon"
        html_content, text_content = format_template(template, context={
            'user_name': "jsmith",
            'user_first': "John",
            'user_last': "Smith",
            'req_id': 1234,
            'req_title': "Project Title",
            'req_team': "Team Name",
            'req_submitted': last_year,
            'req_active': last_year,
            'req_expire': next_week,
            'req_days_left': 7,
            'allocations': (
                {
                    'alloc_cluster': "Cluster 1",
                    'alloc_requested': 100_000,
                    'alloc_awarded': 100_000,
                },
                {
                    'alloc_cluster': "Cluster 2",
                    'alloc_requested': 250_000,
                    'alloc_awarded': 200_000,
                },
            )
        })

        mail = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM_ADDRESS)
        mail.attach_alternative(html_content, "text/html")
        with output_dir.joinpath("upcoming_expiration.eml").open(mode="w") as f:
            f.write(mail.message().as_string())

    @staticmethod
    def _render_past_expiration(output_dir: Path) -> None:
        """Render a sample notification for an allocation request that has expired."""

        today = date.today()
        last_year = today - timedelta(days=365)

        template = get_template("past_expiration.html")
        subject = "Your HPC allocation 1234 has expired"
        html_content, text_content = format_template(template, context={
            'user_name': "jsmith",
            'user_first': "John",
            'user_last': "Smith",
            'req_id': 1234,
            'req_title': "Project Title",
            'req_team': "Team Name",
            'req_active': last_year,
            'req_expire': today,
            'req_submitted': last_year,
            'allocations': (
                {
                    'alloc_cluster': "Cluster 1",
                    'alloc_requested': 100_000,
                    'alloc_awarded': 100_000,
                    'alloc_final': 50_000,
                },
                {
                    'alloc_cluster': "Cluster 2",
                    'alloc_requested': 250_000,
                    'alloc_awarded': 200_000,
                    'alloc_final': 175_000,
                },
            )
        })

        mail = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM_ADDRESS)
        mail.attach_alternative(html_content, "text/html")
        with output_dir.joinpath("past_expiration.eml").open(mode="w") as f:
            f.write(mail.message().as_string())
