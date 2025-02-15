"""Application configuration and initialization.

This module defines application-specific configuration and initialization routines.
It defines application settings and ensures proper application integration within
the parent project.
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
