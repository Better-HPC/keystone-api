from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from plugins.pagination import PaginationHandler


class PaginationHandlerTests(TestCase):
    """Test the paginatation of HTTP response data."""

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.handler = PaginationHandler()
        self.data = list(range(1000))  # Simulated queryset results

    def test_default_limit_and_offset(self) -> None:
        """Verify default values for the pagination limit and offset."""

        request = self.factory.get('/resource/')
        paginated_data = self.handler.paginate_queryset(self.data, Request(request))

        self.assertEqual(len(paginated_data), self.handler.default_limit)
        self.assertEqual(paginated_data[0], 0)

    def test_custom_limit_and_offset(self) -> None:
        """Verify custom limit and offset values are respected."""

        request = self.factory.get('/resource/', {'_limit': '10', '_offset': '20'})
        paginated_data = self.handler.paginate_queryset(self.data, Request(request))

        self.assertEqual(len(paginated_data), 10)
        self.assertEqual(paginated_data[0], 20)

    def test_max_limit_enforced(self) -> None:
        """Verify the maximum limit value is enforced."""

        request = self.factory.get('/resource/', {'_limit': '1000'})
        paginated_data = self.handler.paginate_queryset(self.data, Request(request))

        self.assertEqual(len(paginated_data), self.handler.max_limit)

    def test_paginated_response_headers(self) -> None:
        """Verify pagination metadata is included in response headers."""

        request = self.factory.get('/resource/', {'_limit': '10', '_offset': '30'})
        view_request = Request(request)
        paginated_data = self.handler.paginate_queryset(self.data, view_request)
        response = self.handler.get_paginated_response(paginated_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response['X-Total-Count']), 1000)
        self.assertEqual(int(response['X-Limit']), 10)
        self.assertEqual(int(response['X-Offset']), 30)
        self.assertTrue('X-Next-Page' in response)
        self.assertTrue('X-Previous-Page' in response)

    def test_empty_page(self) -> None:
        request = self.factory.get('/resource/', {'_limit': 100, '_offset': '2000'})
        paginated_data = self.handler.paginate_queryset(self.data, Request(request))
        response = self.handler.get_paginated_response(paginated_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response['X-Total-Count']), 1000)
        self.assertEqual(int(response['X-Limit']), 100)
        self.assertEqual(int(response['X-Offset']), 2000)
        self.assertTrue('X-Next-Page' in response)
        self.assertTrue('X-Previous-Page' in response)

        self.assertEqual(paginated_data, [])
