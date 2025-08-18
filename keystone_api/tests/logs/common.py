"""Common tests for logging endpoints."""

from abc import ABC, abstractmethod
from typing import TypeVar

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from tests.utils import CustomAsserts

TApiTestCase = TypeVar("TApiTestCase", bound=APITestCase)


class LogEndpointPermissionTestMixin(CustomAsserts, ABC):
    """Mixin class used to define common tests for log endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | Authentication             | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User         | 403 | 403  | 403     | 405  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 405  | 405 | 405   | 405    | 405   |
    """

    @property
    @abstractmethod
    def endpoint(self: TApiTestCase) -> str:
        """The API endpoint to test."""

    def setUp(self: TApiTestCase) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

    def test_anonymous_user_permissions(self: TApiTestCase) -> None:
        """Test unauthenticated users cannot access resources."""

        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_permissions(self: TApiTestCase) -> None:
        """Verify authenticated users are returned a 403 status code for all request types."""

        self.client.force_authenticate(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_403_FORBIDDEN,
            head=status.HTTP_403_FORBIDDEN,
            options=status.HTTP_403_FORBIDDEN,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_staff_user_permissions(self: TApiTestCase) -> None:
        """Verify staff users have read-only permissions."""

        self.client.force_authenticate(user=self.staff_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )
