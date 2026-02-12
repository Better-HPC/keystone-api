"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

import logging
import time

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

logger = logging.getLogger(__name__)


def get_ldap_connection() -> 'ldap.ldapobject.LDAPObject':
    """Establish a new LDAP connection."""

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    if settings.AUTH_LDAP_BIND_DN:  # pragma: no branch
        conn.bind(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    if settings.AUTH_LDAP_START_TLS:  # pragma: no branch
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn.start_tls_s()

    conn.set_option(ldap.OPT_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)
    conn.set_option(ldap.OPT_NETWORK_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)
    return conn


def fetch_ldap_data(attempts: int = 3, delay: float = 2.0) -> list:
    """Fetch data from LDAP with retry logic.

    Attempts to connect and fetch data from LDAP up to `attempts` times.
    Retries use exponential backoff, where the wait time doubles after each
    failure (delay, delay*2, delay*4, etc.).

    Args:
        attempts: Maximum number of connection attempts.
        delay: Initial delay in seconds between retries.

    Returns:
        List of LDAP search results.
    """

    if attempts < 1:
        raise RuntimeError("The `attempts` argument must be greater or equal to 1")

    if delay < 0:
        raise RuntimeError("The `delay` argument must be greater or equal to 0")

    for attempt in range(attempts):
        try:
            conn = get_ldap_connection()
            search = conn.search_s(
                settings.AUTH_LDAP_USER_SEARCH.base_dn,
                ldap.SCOPE_SUBTREE,
                settings.AUTH_LDAP_USER_FILTER)

            logger.info(f"Successfully fetched LDAP data on attempt {attempt + 1}")
            return search

        except Exception as e:
            logger.warning(f"LDAP fetch attempt {attempt + 1}/{attempts} failed: {e}")

            if attempt < attempts - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            else:
                logger.error(f"All {attempts} LDAP fetch attempts failed")
                raise


def parse_ldap_entry(dn: str, attrs: dict, attr_map: dict) -> dict | None:
    """Parse an LDAP entry into a dict of Django user fields.

    Args:
        dn: The distinguished name of the LDAP entry.
        attrs: The LDAP attributes for the entry.
        attr_map: Mapping of Django field names to LDAP attribute names.

    Returns:
        A dict of user fields, or None if the entry is invalid.
    """

    # Skip referral entries
    if not dn:
        return None

    ldap_username_attr = attr_map.get('username', 'uid')
    usernames = attrs.get(ldap_username_attr, [])
    if not usernames:
        return None

    username = usernames[0].decode() if isinstance(usernames[0], bytes) else usernames[0]

    user_data = {'username': username, 'is_ldap_user': True, 'is_active': True}
    for django_field, ldap_attr in attr_map.items():
        if django_field == 'username':
            continue

        values = attrs.get(ldap_attr, [])
        if values:
            user_data[django_field] = values[0].decode() if isinstance(values[0], bytes) else values[0]

    return user_data


@shared_task()
def ldap_update_users() -> None:
    """Update the user database with the latest data from LDAP.

    This function does nothing if the `AUTH_LDAP_SERVER_URI` value is not
    configured in application settings.
    """

    if not settings.AUTH_LDAP_SERVER_URI:
        return

    # Search LDAP for all user entries with retry logic
    search = fetch_ldap_data(attempts=3, delay=2.0)

    # Update user data
    ldap_usernames = set()
    for dn, attrs in tqdm(search):
        user_data = parse_ldap_entry(dn, attrs, settings.AUTH_LDAP_USER_ATTR_MAP)
        if not user_data:
            continue

        username = user_data.pop('username')
        ldap_usernames.add(username)

        User.objects.update_or_create(
            username=username,
            defaults=user_data
        )

    # Handle usernames that have been removed from LDAP
    keystone_usernames = set(User.objects.filter(is_ldap_user=True).values_list('username', flat=True))
    removed_usernames = keystone_usernames - ldap_usernames

    if settings.AUTH_LDAP_PURGE_REMOVED:
        User.objects.filter(username__in=removed_usernames).delete()

    else:
        User.objects.filter(username__in=removed_usernames).update(is_active=False)
