"""A Django management command for quickly migrating/deploying a development server.

This management command streamlines development by providing a single command
to handle database migrations, static file collection, and web server deployment.

## Arguments

| Argument    | Description                                                      |
|-------------|------------------------------------------------------------------|
| --all       | Launch all available services.                                   |
| --celery    | Launch a Celery worker with a Redis backend.                     |
| --demo-user | Create an admin user account if no other accounts exist.         |
| --server    | Run the application using a Uvicorn web server.                  |
| --migrate   | Run database migrations.                                         |
| --smtp      | Run an SMTP server using AIOSMTPD.                               |
| --static    | Collect static files.                                            |
"""

import subprocess
from argparse import ArgumentParser
from email.message import EmailMessage

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from . import StdOutUtils


class Command(StdOutUtils, BaseCommand):
    """A helper utility for quickly migrating/deploying an application instance."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments to the parser.

        Args:
            parser: The argument parser instance.
        """

        group = parser.add_argument_group('quickstart options')
        group.add_argument('--all', action='store_true', help='Launch all available services.')
        group.add_argument('--celery', action='store_true', help='Launch a background Celery worker.')
        group.add_argument('--demo-user', action='store_true', help='Create an admin user account if no other accounts exist.')
        group.add_argument('--server', action='store_true', help='Run the application using a Uvicorn web server.')
        group.add_argument('--migrate', action='store_true', help='Run database migrations.')
        group.add_argument('--smtp', action='store_true', help='Run an SMTP server.')
        group.add_argument('--static', action='store_true', help='Collect static files.')

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        if not any([
            options['all'],
            options['celery'],
            options['demo_user'],
            options['server'],
            options['migrate'],
            options['smtp'],
            options['static'],
        ]):
            self.stderr.write('At least one action is required. See `quickstart --help` for details.')
            return

        # Note: `no_input=False` indicates the user should not be prompted for input
        if options['static'] or options['all']:
            self._collect_static()

        if options['migrate'] or options['all']:
            call_command('migrate', interactive=False)

        if options['demo_user'] or options['all']:
            self._create_admin()

        if options['celery'] or options['all']:
            self._run_celery()

        if options['smtp'] or options['all']:
            self._run_smtp()

        if options['server'] or options['all']:
            self._run_server()

    def _collect_static(self) -> None:
        """Collect static application files."""

        self._write("Collecting static files: ", self.style.MIGRATE_HEADING)
        call_command('collectstatic', interactive=False, verbosity=0)
        self._write("  Static files collected.")

    def _create_admin(self) -> None:
        """Create an `admin` user account if no other accounts already exist."""

        self._write("Creating admin user: ", self.style.MIGRATE_HEADING)

        self._write('  Checking for existing users...', ending=' ')
        user = get_user_model()
        if user.objects.exists():
            self._write('User accounts already exist - skipping.', self.style.WARNING)
            return

        self._write('OK', self.style.SUCCESS)

        self._write('  Creating user `admin`...', ending=' ')
        user.objects.create_superuser(username='admin', password='quickstart')
        self._write('OK', self.style.SUCCESS)

    def _run_celery(self) -> None:
        """Start a Celery worker."""

        self._write('Starting Celery services:', self.style.MIGRATE_HEADING)

        self._write('  Launching redis...', ending=' ')
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL)
        self._write('done')

        self._write('  Launching scheduler...', ending=' ')
        subprocess.Popen(['celery', '-A', 'keystone_api.apps.scheduler', 'worker'], stdout=subprocess.DEVNULL)
        self._write('done')

        self._write('  Launching workers...', ending=' ')
        subprocess.Popen(
            ['celery', '-A', 'keystone_api.apps.scheduler', 'beat', '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self._write('done')

    def _run_server(self, host: str = '0.0.0.0', port: int = 8000) -> None:
        """Start a Uvicorn web server.

        Args:
            host: The host to bind to.
            port: The port to bind to.
        """

        self._write("Starting ASGI server: ", self.style.MIGRATE_HEADING)
        command = ['uvicorn', '--host', host, '--port', str(port), 'keystone_api.main.asgi:application']
        subprocess.run(command, check=True)

    def _run_smtp(self, host: str = '0.0.0.0', port: int = 25) -> None:
        """Start an SMTP server.

        Args:
            host: The host to bind to.
            port: The port to bind to.
        """

        self._write("Starting SMTP server: ", self.style.MIGRATE_HEADING)

        class CustomMessageHandler(Message):
            def handle_message(self, message: EmailMessage) -> None:
                print(
                    f"  Received message from: {message['from']}\n"
                    f"  To: {message['to']}\n"
                    f"  Subject: {message['subject']}\n"
                    f"  Body:", message.get_payload()
                )

        controller = Controller(CustomMessageHandler(), hostname=host, port=port)
        controller.start()

        self._write(f"  SMTP server running on {host}:{port}")
