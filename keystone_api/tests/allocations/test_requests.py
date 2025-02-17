"""Function tests for the `/allocations/requests/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.models import AllocationRequest
from apps.users.models import Team, User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | Authentication | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------|-----|------|---------|------|-----|-------|--------|-------|
    | Anonymous User | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    | Non-Member     | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Team Member    | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 403   |
    | Team Admin     | 200 | 200  | 200     | 201  | 403 | 403   | 403    | 403   |
    | Team Owner     | 200 | 200  | 200     | 201  | 403 | 403   | 403    | 403   |
    | Staff User     | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = '/allocations/requests/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and request data from test fixtures."""

        # Load a team of users and define a request endpoint belonging to that team
        self.team = Team.objects.get(name='Team 1')
        self.request = AllocationRequest.objects.filter(team=self.team).first()

        # Load (non)member accounts for the team
        self.staff_user = User.objects.get(username='staff_user')
        self.non_member = User.objects.get(username='generic_user')
        self.team_member = User.objects.get(username='member_1')
        self.team_admin = User.objects.get(username='admin_1')
        self.team_owner = User.objects.get(username='owner_1')

    def test_anonymous_user_permissions(self) -> None:
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
        """Verify users have read access but cannot create records for teams where they are not members."""

        self.client.force_authenticate(user=self.non_member)
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
            post_body={'title': 'foo', 'description': 'bar', 'team' : self.team.pk}
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
            trace=status.HTTP_403_FORBIDDEN,
            post_body={'title': 'foo', 'description': 'bar', 'team' : self.team.pk}
        )

    def test_team_admin_permissions(self) -> None:
        """Verify team admins have read and write access."""

        self.client.force_authenticate(user=self.team_admin)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
            post_body={'title': 'foo', 'description': 'bar', 'team' : self.team.pk}
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read and write access."""

        self.client.force_authenticate(user=self.team_owner)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
            post_body={'title': 'foo', 'description': 'bar', 'team': self.team.pk}
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have read and write permissions."""

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
            post_body={'title': 'foo', 'description': 'bar', 'team': self.team.pk}
        )
