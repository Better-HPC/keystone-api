"""Custom schema generation for DRF Spectacular."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import AutoSchema
from rest_framework.filters import BaseFilterBackend

__all__ = ['FilterGetAutoSchema']


class FilterGetAutoSchema(AutoSchema):
    """Custom OpenApi schema generator that includes filter parameters on `GET` operations.

    By default, DRF Spectacular only includes filter parameters in the OpenAPI
    schema for list endpoints. This custom schema class extends the default
    behavior to include filter parameters on all GET endpoints, including
    detail and custom endpoints.
    """

    def get_filter_backends(self) -> list[BaseFilterBackend | DjangoFilterBackend]:
        """Return the view's filter backends for GET requests, and an empty list otherwise."""

        # The parent class returns an empty list for non-list actions
        # We override to return the view's filter backends for all `GET` operations
        if self.method == "GET":
            return getattr(self.view, 'filter_backends', [])

        return []
