"""Reusable mixin classes for view-level logic and behavior.

Mixins provide composable building blocks for Django REST Framework views.
Each mixin defines a single, isolated piece of functionality and can be
combined with other mixins or base view classes as needed.
"""

from django.db.models import QuerySet

from .models import Team

__all__ = ['TeamScopedListMixin', 'UserScopedListMixin']


class TeamScopedListMixin:
    """Adds team-based filtering to list views based on user access.

    Extends Model Viewset classes by filtering list response data
    based on user team permissions.
    """

    # Name of the model field that links an object to a team.
    # Can be overwritten by subclasses to match the relevant ForeignKey field in a request.
    team_field = 'team'

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by user team membership for list actions."""

        queryset = super().get_queryset()
        if self.action == 'list' and not self.request.user.is_staff:
            teams = Team.objects.teams_for_user(self.request.user)
            return queryset.filter(**{f'{self.team_field}__in': teams})

        return queryset


class UserScopedListMixin:
    """Adds user-based filtering to list views based on the `user` field.

    Extends Model Viewset classes by filtering list response data
    to only include data where the `user` field matches the user submitting
    the request. Staff users are returned all records in the database.
    """

    # Name of the model field that links an object to a team.
    # Can be overwritten by subclasses to match the relevant ForeignKey field in a request.
    user_field = 'user'

    def get_queryset(self) -> QuerySet:
        """Return the base queryset filtered by the requesting user for list actions."""

        queryset = super().get_queryset()
        if self.action == 'list' and not self.request.user.is_staff:
            return queryset.filter(**{self.user_field: self.request.user})

        return queryset
