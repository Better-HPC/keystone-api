"""Reusable mixin classes for view-level logic and behavior.

Mixins provide composable building blocks for Django REST Framework views.
Each mixin defines a single, isolated piece of functionality and can be
combined with other mixins or base view classes as needed.
"""

from rest_framework.request import Request
from rest_framework.response import Response

__all__ = ['UserScopedListMixin']


class UserScopedListMixin:
    """Adds user-based filtering to list views based on the `user` field.

    Extends Model Viewset classes by filtering list response data
    to only include data where the `user` field matches the user submitting
    the request. Staff users are returned all records in the database.
    """

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Return a list of serialized records filtered for the requesting user."""

        if request.user.is_staff:
            query = self.queryset

        else:
            query = self.queryset.filter(user=request.user)

        return Response(self.get_serializer(query, many=True).data)
