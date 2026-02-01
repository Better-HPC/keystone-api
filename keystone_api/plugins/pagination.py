"""Custom pagination handlers for API endpoints.

Pagination classes control how large datasets are divided into paginated
API responses. This includes defining the pagination strategy, default/maximum
page size, and query parameter names used to control pagination.
"""

from rest_framework.pagination import LimitOffsetPagination


class PaginationHandler(LimitOffsetPagination):
    """A limit/offset style pagination for API responses."""

    max_limit = 1_000
    default_limit = 100
    limit_query_param = '_limit'
    offset_query_param = '_offset'
