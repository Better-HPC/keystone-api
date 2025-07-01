"""A Django management command for synchronizing user account data against LDAP.

New accounts are created as necessary and existing accounts are updated to
reflect their corresponding LDAP entries.
"""

from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from apps.users.tasks import ldap_update_users


class Command(BaseCommand):
    """Create or update user accounts to reflect changes made in LDAP."""

    help = 'Create/update user accounts to reflect changes made in LDAP.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-line arguments to the parser.

        Args:
            parser: The argument parser instance.
        """

        parser.add_argument('--prune', action='store_true', help='Delete accounts with usernames not found in LDAP.')

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        try:
            ldap_update_users(prune=options['prune'])

        except KeyboardInterrupt:
            pass
