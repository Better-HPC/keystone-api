"""Clean up files generated when launching a new application instance.

## Arguments

| Argument   | Description                                                      |
|------------|------------------------------------------------------------------|
| --static   | Delete the static root directory                                 |
| --uploads  | Delete all user uploaded file data                               |
| --sqlite   | Delete all SQLite database files                                 |
| --all      | Shorthand for deleting everything                                |
"""

import shutil
from argparse import ArgumentParser
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from . import StdOutUtils


class Command(StdOutUtils, BaseCommand):
    """Clean up files generated when launching a new application instance."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The parser instance to add arguments to.
        """

        group = parser.add_argument_group('clean options')
        group.add_argument('--static', action='store_true', help='Delete the static root directory')
        group.add_argument('--uploads', action='store_true', help='Delete all user uploaded file data')
        group.add_argument('--sqlite', action='store_true', help='Delete all SQLite database files')
        group.add_argument('--all', action='store_true', help='Shorthand for deleting all targets')

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        if not any([options['static'], options['uploads'], options['sqlite'], options['all']]):
            self.stderr.write('At least one deletion target is required. See `clean --help` for details.')
            return

        self._write('Cleaning application data:', self.style.MIGRATE_HEADING)
        if options['static'] or options['all']:
            self._clean_static()

        if options['uploads'] or options['all']:
            self._clean_uploads()

        if options['sqlite'] or options['all']:
            self._clean_sqlite()

    def _clean_static(self) -> None:
        """Remove static application files."""

        self._write('  Removing static files...', ending=' ')
        shutil.rmtree(settings.STATIC_ROOT, ignore_errors=True)
        self._write('OK', self.style.SUCCESS)

    def _clean_uploads(self) -> None:
        """Delete uploaded user files."""

        self._write('  Removing user uploads...', ending=' ')
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        self._write('OK', self.style.SUCCESS)

    def _clean_sqlite(self) -> None:
        """Delete the application's development SQLite database."""

        self._write('  Removing SQLite files...', ending=' ')
        for db_settings in settings.DATABASES.values():
            if 'sqlite' in db_settings['ENGINE']:
                db_path = Path(db_settings['NAME'])
                journal_path = db_path.with_suffix('.db-journal')

                db_path.unlink(missing_ok=True)
                journal_path.unlink(missing_ok=True)

        self._write('OK', self.style.SUCCESS)
