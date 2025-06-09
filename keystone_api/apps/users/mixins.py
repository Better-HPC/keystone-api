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

__all__ = ['ScopedListMixin']


class ScopedListMixin:
    """Adds team-based filtering to list views based on user access.

    Extends Model Viewset classes by filtering list response data
    based on user team permissions.
    """

    # Defined by subclass
    team_field: str

    # Defined by DRF base classes
    queryset: QuerySet
    get_serializer: Callable[..., Serializer]

    def list(self, request: Request) -> Response:
        """Return a list of serialized records filtered by user team permissions."""

        if request.user.is_staff:
            query = self.queryset

        else:
            teams = Team.objects.teams_for_user(request.user)
            query = self.queryset.filter(**{self.team_field + '__in': teams})

        return Response(self.get_serializer(query, many=True).data)
