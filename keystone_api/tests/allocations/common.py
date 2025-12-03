"""Common tests for allocations endpoints."""

from abc import ABC, abstractmethod
from typing import TypeVar

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory

TAPITestCase = TypeVar("TAPITestCase", bound=APITestCase)


class GetResponseContentTests(ABC):
    """Test response content for an authenticated GET request matches the provided content."""

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """The endpoint URL being tested."""

    @property
    @abstractmethod
    def expected_content(self) -> dict:
        """The expected response bopy."""

    def test_returns_expected_content(self: TAPITestCase) -> None:
        """Verify GET responses include the expected content."""

        self.client.force_authenticate(user=UserFactory())

        response = self.client.get(self.endpoint)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.expected_content, response.json())
