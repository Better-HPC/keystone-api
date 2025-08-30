"""Function tests for the `/authentication/login/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | Authentication       | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User | 405 | 405  | 200     | 200  | 405 | 405   | 405    | 405   |
    | Authenticated User   | 405 | 405  | 200     | 200  | 405 | 405   | 405    | 405   |
    """

    endpoint = '/authentication/login/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory(username='user')
        self.user.set_password('foobar123')
        self.user.save()

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users can submit post requests."""

        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_405_METHOD_NOT_ALLOWED,
            head=status.HTTP_405_METHOD_NOT_ALLOWED,
            options=status.HTTP_200_OK,
            post=status.HTTP_200_OK,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'username': 'user', 'password': 'foobar123'},
        )

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users can submit post requests."""

        self.client.force_authenticate(user=self.user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_405_METHOD_NOT_ALLOWED,
            head=status.HTTP_405_METHOD_NOT_ALLOWED,
            options=status.HTTP_200_OK,
            post=status.HTTP_200_OK,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'username': 'user', 'password': 'foobar123'},
        )


class UserAuthentication(APITestCase):
    """Test the user authentication process."""

    login_endpoint = '/authentication/login/'
    whoami_endpoint = '/authentication/whoami/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.password = 'foobar123'
        self.user = UserFactory(username='user', password=self.password)

    def test_invalid_credentials(self) -> None:
        """Verify user authentication fails with invalid credentials."""

        # Verify the auth request returns a failure status
        auth_response = self.client.post(self.login_endpoint, {'username': self.user.username, 'password': 'wrong'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, auth_response.status_code)

        # Verify the API reports an unauthenticated user session
        whoami_response = self.client.get(self.whoami_endpoint)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, whoami_response.status_code)

    def test_valid_credentials(self) -> None:
        """Verify user authentication succeeds with valid credentials."""

        # Verify the auth request returns a successful status
        auth_response = self.client.post(self.login_endpoint, {'username': self.user.username, 'password': self.password})
        self.assertEqual(status.HTTP_200_OK, auth_response.status_code)

        # Verify the API reports an authenticated user session
        whoami_response = self.client.get(self.whoami_endpoint)
        self.assertEqual(status.HTTP_200_OK, whoami_response.status_code)
