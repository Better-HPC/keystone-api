"""Health check backends for verifying the status of supporting services.

This module defines custom health checks for supporting application services.
These checks supplement third-party health checks that come bundled with the
`django-health-check` package.
"""

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import get_connection
from health_check.backends import BaseHealthCheckBackend


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
