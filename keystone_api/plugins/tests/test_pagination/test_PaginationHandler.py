"""Unit tests for the `PaginationHandler` class."""

from django.test import TestCase
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from plugins.pagination import PaginationHandler


class PaginateQuerysetMethod(TestCase):
    """Test the slicing of paginated data."""

    def setUp(self) -> None:
        """Initialize test fixtures."""

        self.factory = APIRequestFactory()
        self.pagination = PaginationHandler()
        self.data = list(range(10))  # test dataset

    def test_returns_all_values_by_default(self) -> None:
        """Verify all values are returned when no pagination params are provided."""

        request = self.factory.get("/")
        paginated = self.pagination.paginate_queryset(self.data, Request(request), view=None)

        # If no limit/offset given and no default_limit set, pagination should not slice
        self.assertEqual(self.data, paginated)

    def test_returns_correct_values_with_pagination(self) -> None:
        """Verify the correct subset of values is returned when pagination params are provided."""

        request = self.factory.get("/", {"_limit": 3, "_offset": 4})
        paginated = self.pagination.paginate_queryset(self.data, Request(request), view=None)

        # Expect slice starting at index 4, of length 3
        self.assertEqual([4, 5, 6], paginated)


class Test(TestCase):
    """Test header values in paginated responses."""

    def setUp(self) -> None:
        """Initialize test fixtures."""

        self.factory = APIRequestFactory()
        self.pagination = PaginationHandler()
        self.data = list(range(10))

    def test_paginated_response_headers(self) -> None:
        """Verify paginated responses include pagination headers."""

        request = self.factory.get("/", {"_limit": 2, "_offset": 1})
        paginated = self.pagination.paginate_queryset(self.data, Request(request), view=None)
        response = self.pagination.get_paginated_response(paginated)

        # Verify response status
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 200)

        # Verify headers are present
        self.assertIn("X-Total-Count", response)
        self.assertIn("X-Limit", response)
        self.assertIn("X-Offset", response)

        # Verify header values
        self.assertEqual('10', response["X-Total-Count"])
        self.assertEqual('2', response["X-Limit"])
        self.assertEqual('1', response["X-Offset"])
