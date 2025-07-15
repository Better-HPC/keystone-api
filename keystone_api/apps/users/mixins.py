"""Reusable mixin classes for view-level logic and behavior.

Mixins provide composable building blocks for Django REST Framework views.
Each mixin defines a single, isolated piece of functionality and can be
combined with other mixins or base view classes as needed.
"""

from typing import Callable

from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

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

    # Defined by DRF base classes
    queryset: QuerySet
    get_serializer: Callable[..., Serializer]

    def list(self, request: Request) -> Response:
        """Return a list of serialized records filtered by user team permissions."""

        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.is_staff:
            teams = Team.objects.teams_for_user(request.user)
            queryset = queryset.filter(**{self.team_field + '__in': teams})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserScopedListMixin:
    """Adds user-based filtering to list views based on the `user` field.

    Extends Model Viewset classes by filtering list response data
    to only include data where the `user` field matches the user submitting
    the request. Staff users are returned all records in the database.
    """

    # Name of the model field that links an object to a team.
    # Can be overwritten by subclasses to match the relevant ForeignKey field in a request.
    user_field = 'user'

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Return a list of serialized records filtered for the requesting user."""

        queryset = self.filter_queryset(self.get_queryset())

        if not request.user.is_staff:
            queryset = queryset.filter(**{self.user_field: request.user})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
