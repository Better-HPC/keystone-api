"""A Django management command for synchronizing user account data against LDAP.

New accounts are created as necessary and existing accounts are updated to
reflect their corresponding LDAP entries.
"""

from django.core.management.base import BaseCommand

from apps.users.tasks import ldap_update_users


class Command(BaseCommand):
    """Synchronize user accounts against LDAP."""

    help = "Synchronize user accounts against LDAP."

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        try:
            ldap_update_users()

        except KeyboardInterrupt:
            pass
