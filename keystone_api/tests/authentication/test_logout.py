"""Function tests for the `/authentication/logout/` endpoint."""

from django.contrib.auth import login
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from apps.users.models import User
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
    fixtures = ['testing_common.yaml']

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
        """Verify authenticated users post logout requests."""

        user = User.objects.get(username='generic_user')
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
