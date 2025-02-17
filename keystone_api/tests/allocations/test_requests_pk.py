"""Function tests for the `/allocations/requests/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.models import AllocationRequest
from apps.users.models import Team, User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    | Authenticated non-member   | 404 | 404  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Team member                | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Team admin                 | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Team owner                 | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint = '/allocations/requests/1/'
    endpoint_pattern = '/allocations/requests/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and request data from test fixtures."""

        # Load a team of users and define a request endpoint belonging to that team
        self.team = Team.objects.get(name='Team 1')
        self.request = AllocationRequest.objects.filter(team=self.team).first()
        self.endpoint = self.endpoint_pattern.format(pk=self.request.pk)

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
            get=status.HTTP_403_FORBIDDEN,
            head=status.HTTP_403_FORBIDDEN,
            options=status.HTTP_403_FORBIDDEN,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_non_team_member_permissions(self) -> None:
        """Verify users cannot access records for a team they are not in."""

        self.client.force_authenticate(user=self.non_member)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_404_NOT_FOUND,
            head=status.HTTP_404_NOT_FOUND,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_team_member_permissions(self) -> None:
        """Verify regular team members have read-only access."""

        self.client.force_authenticate(user=self.team_member)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_team_admin_permissions(self) -> None:
        """Verify team admins have read-only access."""

        self.client.force_authenticate(user=self.team_admin)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read-only access."""

        self.client.force_authenticate(user=self.team_owner)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        self.client.force_authenticate(user=self.staff_user)
        record_data = {'title': 'foo', 'description': 'bar', 'team': self.team.pk}

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
            put_body=record_data,
            patch_data=record_data
        )
