"""Application level configuration and setup.

Application configuration objects are used to override Django's default
application setup. They define application metadata and ensure proper
integration with the parent project.
"""

from django.apps import AppConfig

from health_check.plugins import plugin_dir


class HealthAppConfig(AppConfig):
    """Django configuration for the `scheduler` app."""

    name = 'apps.health'

    def ready(self) -> None:
        """Setup tasks executed after loading the application configuration and models"""

        from .backends import SMTPHealthCheck
        plugin_dir.register(SMTPHealthCheck)
