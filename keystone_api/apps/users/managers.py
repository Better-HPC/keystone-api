"""Custom database managers for encapsulating repeatable table queries.

Manager classes encapsulate common database operations at the table level (as
opposed to the level of individual records). At least one Manager exists for
every database model. Managers are commonly exposed as an attribute of the
associated model class called `objects`.
"""

from typing import TYPE_CHECKING

from django.contrib.auth import password_validation
from django.contrib.auth.base_user import BaseUserManager
from django.db import models

if TYPE_CHECKING:  # pragma: nocover
    from apps.users.models import User

__all__ = ['TeamManager', 'UserManager']


class TeamManager(models.Manager):
    """Object manager for the `Team` database model."""

    def teams_for_user(self, user: 'User') -> models.QuerySet:
        """Get all teams the user is affiliated with.

        Args:
            user: The user to return affiliate teams for.

        Returns:
            A filtered queryset.
        """

        return self.filter(membership__user=user)


class UserManager(BaseUserManager):
    """Object manager for the `User` database model."""

    def create_user(self, username: str, password: str, **extra_fields) -> 'User':
        """Create a new user account.

        Args:
            username: The account username.
            password: The account password.
            **extra_fields: See fields of the `models.User` class for other accepted arguments.

        Returns:
            The saved user account.
        """

        if 'email' in extra_fields:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])

        password_validation.validate_password(password)

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username: str, password: str, **extra_fields) -> 'User':
        """Create a new user account with superuser privileges.

        Args:
            username: The account username.
            password: The account password.
            **extra_fields: See fields of the `models.User` class for other accepted arguments.

        Returns:
            The saved user account.
        """

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('When creating a superuser you must set `is_staff=True`.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('When creating a superuser you must set  `is_superuser=True`.')

        return self.create_user(username, password, **extra_fields)
