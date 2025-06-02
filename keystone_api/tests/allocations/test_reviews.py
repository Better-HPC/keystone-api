"""Function tests for the `/allocations/reviews/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User         | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = '/allocations/reviews/'
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

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users have read-only permissions."""

        self.client.force_authenticate(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
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
            post_body={'status': 'AP', 'request': 1}
        )


class ReviewerAssignment(APITestCase):
    """Test the automatic assignment and verification of the `reviewer` field."""

    endpoint = '/allocations/reviews/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts from test fixtures."""

        self.generic_user = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

    def test_default_reviewer(self) -> None:
        """Verify the reviewer field defaults to the current user."""

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.endpoint, {'request': 1, 'status': 'AP'})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.staff_user.id, response.data['reviewer'])

    def test_reviewer_provided(self) -> None:
        """Verify the reviewer is set correctly when provided."""

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.endpoint, {'request': 1, 'reviewer': self.staff_user.id, 'status': 'AP'})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.staff_user.id, response.data['reviewer'])

    def test_error_when_not_matching_submitter(self) -> None:
        """Verify an error is raised when the reviewer field does not match the request submitter."""

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.endpoint, {'request': 1, 'reviewer': self.generic_user.id, 'status': 'AP'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reviewer', response.data)
        self.assertEqual('reviewer cannot be set to a different user than the submitter', response.data['reviewer'][0].lower())
