"""Health check backends for verifying the status of supporting services.

This module defines custom health checks for supporting application services.
These checks supplement the built-in health checks provided by the
`django-health-check` package.
"""

import dataclasses

from django.conf import settings
from health_check.base import HealthCheck
from health_check.exceptions import ServiceUnavailable

__all__ = ["LDAPHealthCheck"]


@dataclasses.dataclass
class LDAPHealthCheck(HealthCheck):
    """Custom health check for LDAP connectivity.

    Performs an LDAP `whoami` query to verify server availability using
    the LDAP connection parameters defined in application settings.
    """

    def run(self) -> None:
        """Perform an LDAP `whoami` query to verify server availability."""

        import ldap

        try:
            conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
            conn.set_option(ldap.OPT_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, settings.AUTH_LDAP_TIMEOUT)

            if settings.AUTH_LDAP_BIND_DN:
                conn.bind(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

            if settings.AUTH_LDAP_START_TLS:
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                conn.start_tls_s()

            conn.whoami_s()

        except ldap.INVALID_CREDENTIALS as e:
            raise ServiceUnavailable("Invalid LDAP credentials.") from e

        except ldap.SERVER_DOWN as e:
            raise ServiceUnavailable("LDAP server not reachable.") from e

        except Exception as e:
            raise ServiceUnavailable("Unexpected error") from e
