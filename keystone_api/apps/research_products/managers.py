"""Custom database managers for encapsulating repeatable table queries.

Manager classes encapsulate common database operations at the table level (as
opposed to the level of individual records). At least one Manager exists for
every database model. Managers are commonly exposed as an attribute of the
associated model class called `objects`.
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Manager

from apps.users.models import Team

__all__ = ['GrantManager', 'PublicationManager']


class BaseManager(Manager):
    """Base manager class for encapsulating common database operations."""

    def affiliated_with_user(self, user: User) -> models.QuerySet:
        """Get all allocation requests affiliated with the given user.

        Args:
            user: The user to return affiliated records for.

        Returns:
            A filtered queryset of records affiliated with the given user.
        """

        teams = Team.objects.teams_for_user(user)
        return self.get_queryset().filter(team__in=teams)


class GrantManager(BaseManager):
    """Object manager for the `Grant` database model."""


class PublicationManager(BaseManager):
    """Object manager for the `Publication` database model."""
