"""Application level configuration and setup.

Application configuration objects are used to override Django's default
application setup. They define application metadata and ensure proper
integration with the parent project.
"""

from django.apps import AppConfig
from django.core.checks import register

from .checks import *

__all__ = ['SchedulerAppConfig']


class SchedulerAppConfig(AppConfig):
    """Django configuration for the `scheduler` app."""

    name = 'apps.scheduler'

    def ready(self) -> None:
        """Setup tasks executed after loading the application configuration and models"""

        register(check_celery_beat_configuration)
