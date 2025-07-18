"""Function tests for the `/notifications/preferences/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.factories import PreferenceFactory
from apps.users.factories import UserFactory
from tests.utils import CustomAsserts, UserScopedListFilteringTests

ENDPOINT = '/notifications/preferences/'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status          | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User   | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff User Accessing | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

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

    def test_authenticated_user(self) -> None:
        """Verify authenticated users can access and modify their own records."""

        self.client.force_authenticate(self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have read-only permissions."""

        self.client.force_authenticate(self.staff_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class UserFieldAssignment(APITestCase):
    """Test the automatic assignment and verification of the `user` field."""

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user1 = UserFactory(is_staff=False)
        self.user2 = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

    def test_default_user(self) -> None:
        """Verify the user field defaults to the current user."""

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.endpoint)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.user1.id, response.data['user'])

    def test_user_provided(self) -> None:
        """Verify the user field is set correctly when provided."""

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.endpoint, {'user': self.user1.id})

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.user1.id, response.data['user'])

    def test_error_when_not_matching_submitter(self) -> None:
        """Verify an error is raised when the user field does not match the request submitter."""

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.endpoint, {'user': self.user2.id})

        expected_error = 'user field cannot be set to a different user than the request submitter.'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.data['user'][0].lower())

    def test_staff_can_override_field(self) -> None:
        """Verify staff users can create records on behalf of other users."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.endpoint, {'user': self.user2.id})

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.user2.id, response.data['user'])


class RecordFiltering(UserScopedListFilteringTests, APITestCase):
    """Test the filtering of returned records based on user ownership."""

    endpoint = ENDPOINT
    factory = PreferenceFactory
