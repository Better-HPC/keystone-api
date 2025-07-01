"""System checks used to validate package configuration.

System checks are used to detect common problems and provide hints on
how to fix them. Checks are automatically run during various deployment
tasks, including database migration and server launch.
"""

from django.conf import settings
from django.core.checks import Error


def ldap_dependency_check(*args, **kwargs) -> list[Error]:
    """Check if LDAP dependencies are required and installed.

    Returns:
        A list of identified errors.
    """

    errors = []

    try:
        import ldap
        ldap_installed = True

    except ImportError:
        ldap_installed = False

    if settings.AUTH_LDAP_SERVER_URI and not ldap_installed:
        errors.append(
            Error(
                "LDAP authentication is enabled but LDAP dependencies are not installed.",
                hint="Disable LDAP authentication or reinstall the package with the [ldap] extra.",
                id="users.E001",
            )
        )

    return errors
