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
    detail views and custom endpoints.
    """

    def get_filter_backends(self) -> list[BaseFilterBackend | DjangoFilterBackend]:
        """Return filter backends for all endpoints, not just list endpoints.

        The parent class implementation returns an empty list for non-list
        actions. This override ensures that the view's configured filter
        backends are always returned, enabling filter parameter generation
        for detail endpoints and custom views.

        Returns:
            A list of filter backend classes configured on the view, or an
            empty list if no filter backends are defined.
        """

        # The parent class returns an empty list for non-list actions
        # We override to always return the view's filter backends
        if hasattr(self.view, 'filter_backends'):
            return self.view.filter_backends

        return []

    def allows_filters(self, path: str, method: str) -> bool:
        """Allow filters on all GET endpoints, not just list endpoints.

        The parent class implementation restricts filter parameters to list
        actions only. This override enables filters on all GET requests,
        allowing detail views and custom endpoints to expose their filter
        parameters in the generated OpenAPI schema.

        Args:
            path: The URL path being documented.
            method: The HTTP method (e.g., 'GET', 'POST', 'PUT').

        Returns:
            True if the method is GET, otherwise delegates to the parent
            implementation for other HTTP methods.
        """

        if method.upper() == 'GET':
            return True

        return super().allows_filters(path, method)
