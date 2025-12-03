"""Function tests for the `users:team-list` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from tests.utils import CustomAsserts

VIEW_NAME = 'users:team-list'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated user         | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff user                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory()
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

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users can create new teams."""

        self.client.force_authenticate(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'name': 'New Name'}
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        self.client.force_authenticate(user=self.staff_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'name': 'New Name'},
        )


class SlugHandling(APITestCase, CustomAsserts):
    """Test slug value handling on team creation."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Authenticate a generic user."""

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_slug_set_automatically(self) -> None:
        """Verify a slug is automatically generated from the team name."""

        response = self.client.post(self.endpoint, {"name": "My New Team"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("slug", response.data)
        self.assertEqual("my-new-team", response.data["slug"])

    def test_manual_slug_ignored(self) -> None:
        """Verify manually provided slug values are ignored."""

        response = self.client.post(self.endpoint, {"name": "Manual Slug Test", "slug": "wrong-slug"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual("manual-slug-test", response.data["slug"])

    def test_slug_uniqueness_enforced(self) -> None:
        """Verify users cannot create teams with the different names but the same slug."""

        # Creating the first team should succeed
        response1 = self.client.post(self.endpoint, {"name": "Team X"})
        self.assertEqual(status.HTTP_201_CREATED, response1.status_code)

        # Creating a team with a name that slugifies into a non-unique value should fail
        response2 = self.client.post(self.endpoint, {"name": "Team-X"})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response2.status_code)
