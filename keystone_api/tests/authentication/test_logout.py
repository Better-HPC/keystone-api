"""Function tests for the `/authentication/logout/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | Authentication       | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User   | 405 | 405  | 200     | 200  | 405 | 405   | 405    | 405   |
    """

    endpoint = '/authentication/logout/'

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access the endpoint."""

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
        """Verify authenticated users can submit post requests."""

        user = UserFactory(is_staff=False)
        self.client.force_authenticate(user=user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_405_METHOD_NOT_ALLOWED,
            head=status.HTTP_405_METHOD_NOT_ALLOWED,
            options=status.HTTP_200_OK,
            post=status.HTTP_200_OK,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class UserAuthentication(APITestCase):
    """Test the process of logging out users."""

    login_endpoint = '/authentication/login/'
    logout_endpoint = '/authentication/logout/'
    whoami_endpoint = '/authentication/whoami/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.password = 'foobar123'
        self.user = UserFactory(username='user', password=self.password, is_staff=False)

    def assert_authentication(self, auth_status: bool) -> None:
        """Assert whether the current client session is authenticated.

        If auth_status is True, assert the current client session is authenticated.
        If auth_status is False, assert the current client session is not authenticated.

        Args:
            auth_status: The  authenticated state to test for.
        """

        auth_status_code = {
            True: status.HTTP_200_OK,
            False: status.HTTP_401_UNAUTHORIZED,
        }[auth_status]

        # Query the current user authentication state from the API
        whoami_response = self.client.get(self.whoami_endpoint)
        self.assertEqual(auth_status_code, whoami_response.status_code)

    def test_authenticated_session(self) -> None:
        """Verify currently authenticated users are successfully logged out."""

        self.client.post(self.login_endpoint, {'username': self.user.username, 'password': self.password})
        self.assert_authentication(True)

        self.client.post(self.logout_endpoint)
        self.assert_authentication(False)

    def test_unauthenticated_session(self) -> None:
        """Verify unauthenticated users are returned a 401 Status."""

        logout_request = self.client.post(self.logout_endpoint)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, logout_request.status_code)
        self.assert_authentication(auth_status=False)
