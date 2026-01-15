"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

from celery import shared_task
from django.conf import settings
from tqdm import tqdm

from .models import User

# Optional dependencies
try:
    import ldap

except ImportError:  # pragma: nocover
    pass

__all__ = ['ldap_update_users']


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
def ldap_update_users() -> None:
    """Update the user database with the latest data from LDAP.

    This function does nothing if the `AUTH_LDAP_SERVER_URI` value is not
    configured in application settings.
    """

    if not settings.AUTH_LDAP_SERVER_URI:
        return

    # Search LDAP for all user entries
    conn = get_ldap_connection()
    conn.set_option(ldap.OPT_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)
    conn.set_option(ldap.OPT_NETWORK_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)

    search = conn.search_s(settings.AUTH_LDAP_USER_SEARCH.base_dn, ldap.SCOPE_SUBTREE, settings.AUTH_LDAP_USER_FILTER)

    # Fetch LDAP usernames using the LDAP attribute map defined in settings
    attr_map = settings.AUTH_LDAP_USER_ATTR_MAP
    ldap_username_attr = attr_map.get('username', 'uid')
    ldap_names = {uid.decode() for result in search for uid in result[1][ldap_username_attr]}

    # Update user data
    for dn, attrs in tqdm(search):
        if not dn:
            continue

        usernames = attrs.get(ldap_username_attr, [])
        if not usernames:
            continue

        username = usernames[0].decode() if isinstance(usernames[0], bytes) else usernames[0]

        # Build user fields from LDAP attributes
        user_data = {'is_ldap_user': True, 'is_active': True}
        for django_field, ldap_attr in attr_map.items():
            if django_field == 'username':
                continue

            values = attrs.get(ldap_attr, [])
            if values:
                user_data[django_field] = values[0].decode() if isinstance(values[0], bytes) else values[0]

        User.objects.update_or_create(
            username=username,
            defaults=user_data
        )

    # Handle usernames that have been removed from LDAP
    keystone_names = set(User.objects.filter(is_ldap_user=True).values_list('username', flat=True))
    removed_usernames = keystone_names - ldap_names

    if settings.AUTH_LDAP_PURGE_REMOVED:
        User.objects.filter(username__in=removed_usernames).delete()

    else:
        User.objects.filter(username__in=removed_usernames).update(is_active=False)
