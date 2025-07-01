"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

from celery import shared_task
from django.conf import settings
from tqdm import tqdm

# Optional dependencies
try:
    import ldap
    from django_auth_ldap.backend import LDAPBackend

except ImportError:  # pragma: nocover
    pass


def get_ldap_connection() -> 'ldap.ldapobject.LDAPObject':
    """Establish a new LDAP connection."""

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    if settings.AUTH_LDAP_BIND_DN:  # pragma: no branch
        conn.bind(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    if settings.AUTH_LDAP_START_TLS:  # pragma: no branch
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn.start_tls_s()

    return conn


@shared_task()
def ldap_update_users(prune: bool = settings.PURGE_REMOVED_LDAP_USERS) -> None:
    """Update the user database with the latest data from LDAP.

    This function does nothing if the `AUTH_LDAP_SERVER_URI` value is not
    configured in application settings.

    Args:
        prune: Optionally delete accounts with usernames no longer found in LDAP.
    """

    if not settings.AUTH_LDAP_SERVER_URI:
        return

    # Search LDAP for all user entries
    conn = get_ldap_connection()
    search = conn.search_s(settings.AUTH_LDAP_USER_SEARCH.base_dn, ldap.SCOPE_SUBTREE, '(objectClass=account)')

    # Fetch LDAP usernames using the LDAP attribute map defined in settings
    ldap_username_attr = settings.AUTH_LDAP_USER_ATTR_MAP.get('username', 'uid')
    ldap_names = {uid.decode() for result in search for uid in result[1][ldap_username_attr]}

    # Update user data
    backend = LDAPBackend()
    for username in tqdm(ldap_names):
        user = backend.populate_user(username)
        if user is not None:  # pragma: no branch
            user.is_ldap_user = True
            user.save()

    # Handle usernames that have been removed from LDAP
    from .models import User
    keystone_names = set(User.objects.filter(is_ldap_user=True).values_list('username', flat=True))
    removed_usernames = keystone_names - ldap_names

    if prune:
        User.objects.filter(username__in=removed_usernames).delete()

    else:
        User.objects.filter(username__in=removed_usernames).update(is_active=False)
