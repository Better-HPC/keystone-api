"""Function tests for the `/notifications/preferences/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.factories import PreferenceFactory
from apps.users.factories import UserFactory
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                               | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |-------------------------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User                      | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User Accessing Own Data     | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Authenticated User Accessing Other's Data | 403 | 403  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Staff User Accessing Other's Data         | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = '/notifications/preferences/{pk}/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.preference_user = UserFactory()
        self.generic_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.preference = PreferenceFactory(user=self.preference_user)

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        endpoint = self.endpoint_pattern.format(pk=self.preference_user.id)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_same_user(self) -> None:
        """Verify authenticated users can access and modify their own records."""

        # Define a user / record endpoint for the SAME user
        endpoint = self.endpoint_pattern.format(pk=self.preference.id)
        self.client.force_authenticate(user=self.preference_user)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_authenticated_user_different_user(self) -> None:
        """Verify users cannot modify other users' records."""

        # Define a user / record endpoint for DIFFERENT users
        endpoint = self.endpoint_pattern.format(pk=self.preference.id)
        self.client.force_authenticate(user=self.generic_user)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_403_FORBIDDEN,
            head=status.HTTP_403_FORBIDDEN,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users can modify other users' records."""

        endpoint = self.endpoint_pattern.format(pk=self.preference.id)
        self.client.force_authenticate(user=self.staff_user)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
