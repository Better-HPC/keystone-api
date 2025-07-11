"""Function tests for the `/authentication/login/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
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
        """Create a user account to use when testing authentication."""

        self.user = User.objects.create_user(username='user', password='foobar123')

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access the endpoint."""

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
        """Verify authenticated users post logout requests."""

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
