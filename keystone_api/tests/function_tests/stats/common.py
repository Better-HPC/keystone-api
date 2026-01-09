"""Common tests for statistics endpoints."""

from abc import ABC, abstractmethod

from rest_framework import status

from apps.users.factories import UserFactory
from tests.function_tests.utils import CustomAsserts


class StatisticEndpointPermissionsTestMixin(CustomAsserts, ABC):
    """Test user permissions for list endpoints.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team Member                | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team Admin                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team Owner                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """The API endpoint to test."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory()

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

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

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated have read only permissions."""

        self.client.force_login(user=self.generic_user)
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
