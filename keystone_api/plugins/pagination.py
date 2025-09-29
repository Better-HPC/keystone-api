"""Provides custom pagination handlers for API endpoints.

Pagination classes determine how large datasets are divided and delivered in
paginated API responses. This plugin customizes the default limit/offset
pagination strategy, including default and maximum limits, and overrides the
query parameter names used to control pagination.
"""

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class PaginationHandler(LimitOffsetPagination):
    """A limit/offset style pagination for API responses."""

    max_limit = 1_000
    default_limit = 100
    limit_query_param = '_limit'
    offset_query_param = '_offset'

    def get_paginated_response(self, data: list) -> Response:
        """Format response data as a paginated HTTP response object.

        Args:
            data: The data to include in the paginated response.

        Returns:
            An HTTP response including paginated data and pagination headers.
        """

        response = Response(data)
        response['X-Limit'] = self.limit
        response['X-Offset'] = self.offset
        response['X-Total-Count'] = self.count
        return response
