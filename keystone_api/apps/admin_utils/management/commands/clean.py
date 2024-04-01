"""Clean up files generated when launching a new application instance.

## Arguments

| Argument   | Description                                                      |
|------------|------------------------------------------------------------------|
| --static   | Delete the static root directory                                 |
| --uploads  | Delete all user uploaded file data                              |
| --db       | Delete all sqlite database files                                 |
| --all      | Shorthand for deleting everything                                |
"""

import shutil
from argparse import ArgumentParser
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """A helper utility that wraps common Django deployment tasks"""

    help = 'A helper utility for deploying a development application instance.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments

        Args:
          parser: The parser instance to add arguments under
        """

        group = parser.add_argument_group('clean options')
        group.add_argument('--static', action='store_true', help='Delete the static root directory')
        group.add_argument('--uploads', action='store_true', help='Delete all user uploaded file data')
        group.add_argument('--db', action='store_true', help='Delete all sqlite database files')
        group.add_argument('--all', action='store_true', help='Shorthand for deleting all targets')

    def handle(self, *args, **options) -> None:
        """Handle the command execution.

        Args:
          *args: Additional positional arguments.
          **options: Additional keyword arguments.
        """

        if not any([options['static'], options['db'], options['all']]):
            self.stderr.write('At least one deletion target is required. `See clean --help` for details.')

        if options['static'] or options['all']:
            self.stdout.write(self.style.SUCCESS('Removing static files...'))
            shutil.rmtree(settings.STATIC_ROOT, ignore_errors=True)

        if options['uploads'] or options['all']:
            self.stdout.write(self.style.SUCCESS('Removing user uploads...'))
            shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

        if options['db'] or options['all']:
            self.stdout.write(self.style.SUCCESS('Removing sqlite files...'))
            for db_settings in settings.DATABASES.values():
                if 'sqlite' in db_settings['ENGINE']:
                    Path(db_settings['NAME']).unlink(missing_ok=True)
