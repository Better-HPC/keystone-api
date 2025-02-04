"""Application level configuration and setup.

Application configuration objects are used to override Django's default
application setup.
"""

from django.apps import AppConfig
from django.core.checks import register

from . import checks

__all__ = ['UsersAppConfig']


class UsersAppConfig(AppConfig):
    """General application configuration and metadata."""

    name = 'apps.users'

    def ready(self) -> None:
        """Register application specific system checks."""

        register(checks.ldap_dependency_check)
