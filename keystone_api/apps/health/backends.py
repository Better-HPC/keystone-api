"""Health check backends for verifying the status of supporting services.

This module defines custom health checks for supporting application services.
These checks supplement third-party health checks that come bundled with the
`django-health-check` package.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import get_connection
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException


class LDAPHealthCheck(BaseHealthCheckBackend):
    """Custom health check backend for LDAP connectivity."""

    def check_status(self) -> None:
        """Perform a simple LDAP bind to verify server availability."""

        import ldap

        try:
            conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
            if settings.AUTH_LDAP_BIND_DN:  # pragma: no branch
                conn.bind(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

            if settings.AUTH_LDAP_START_TLS:  # pragma: no branch
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                conn.start_tls_s()

            conn.whoami_s()

        except ldap.INVALID_CREDENTIALS:
            raise HealthCheckException("Invalid LDAP credentials.")

        except ldap.SERVER_DOWN:
            raise HealthCheckException("LDAP server not reachable.")

        except Exception:
            raise HealthCheckException(f"Unexpected error")


class SMTPHealthCheck(BaseHealthCheckBackend):
    """Health check plugin for the SMTP server defined in application settings."""

    def check_status(self) -> None:
        """Check the status of the SMTP server."""

        connection = None

        try:
            connection = get_connection(fail_silently=False)

            # Check if the connection is configured in settings
            if not connection.host:
                raise ImproperlyConfigured("Email backend is not configured.")

            # Check if the server is accessible
            connection.open()
            connection.connection.noop()

        except ImproperlyConfigured as e:
            self.add_error("Email backend is not configured properly.", e)

        except Exception as e:
            self.add_error(str(e), e)

        finally:
            if connection:  # pragma: no branch
                connection.close()
