"""Function tests for the `/allocations/requests/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.models import AllocationRequest, Comment
from apps.users.models import Team, User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 403 | 403  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member                | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Team admin                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Team owner                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = '/allocations/comments/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and request data from test fixtures."""

        # Load a team of users and define a request endpoint belonging to that team
        self.team = Team.objects.get(name='Team 1')
        self.request = AllocationRequest.objects.filter(team=self.team).first()
        self.comment = Comment.objects.filter(request=self.request).first()
        self.endpoint = self.endpoint_pattern.format(pk=self.comment.pk)
        self.record_data = {'content': 'foobar', 'request': self.request.pk}


        # Load (non)member accounts for the team
        self.staff_user = User.objects.get(username='staff_user')
        self.non_member = User.objects.get(username='generic_user')
        self.team_member = User.objects.get(username='member_1')
        self.team_admin = User.objects.get(username='admin_1')
        self.team_owner = User.objects.get(username='owner_1')

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

    def test_non_team_member_permissions(self) -> None:
        """Verify users cannot access records for a team they are not in."""

        self.client.force_authenticate(user=self.non_member)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_403_FORBIDDEN,
            head=status.HTTP_403_FORBIDDEN,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_team_member_permissions(self) -> None:
        """Verify regular team members have read-only access."""

        self.client.force_authenticate(user=self.team_member)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body=self.record_data,
            patch_data=self.record_data
        )

    def test_team_admin_permissions(self) -> None:
        """Verify team admins have read-only access."""

        self.client.force_authenticate(user=self.team_admin)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body=self.record_data,
            patch_data=self.record_data
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read-only access."""

        self.client.force_authenticate(user=self.team_owner)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body=self.record_data,
            patch_data=self.record_data
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        self.client.force_authenticate(user=self.staff_user)

        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body=self.record_data,
            patch_data=self.record_data
        )
