from rest_framework.pagination import LimitOffsetPagination


class PaginationHandler(LimitOffsetPagination):
    default_limit = 100
    limit_query_param = '_limit'
    offset_query_param = '_offset'
    max_limit = 1000
