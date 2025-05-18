"""Function tests for the `/notifications/preferences/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                             | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |-----------------------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User                    | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User Accessing Own Data   | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Authenticated User Accessing Other Data | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    | Staff User                              | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    """

    endpoint = '/notifications/preferences/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts from test fixtures."""

        self.generic_user = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

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

    def test_authenticated_user_same_user(self) -> None:
        """Verify authenticated users can access and modify their own records."""

        # Todo
        self.fail()

    def test_authenticated_user_different_user(self) -> None:
        """Verify users cannot modify other users' records."""

        # Todo
        self.fail()

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have read-only permissions."""

        # Todo
        self.fail()
