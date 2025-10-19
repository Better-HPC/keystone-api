"""Function tests for the `/users/teams/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership
from tests.utils import CustomAsserts

ENDPOINT_PATTERN = '/users/teams/{pk}/'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member                | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team admin                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Team owner                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = ENDPOINT_PATTERN

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory()
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user

        self.non_team_member = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.team_endpoint = self.endpoint_pattern.format(pk=self.team.pk)

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_non_member_permissions(self) -> None:
        """Verify non-members have read-only permissions."""

        self.client.force_authenticate(user=self.non_team_member)
        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_team_member_permissions(self) -> None:
        """Verify team members have read-only permissions."""

        self.client.force_authenticate(user=self.team_member)
        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_team_admin_permissions(self) -> None:
        """Verify team admins have read and write permissions."""

        self.client.force_authenticate(user=self.team_admin)
        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={'name': 'New Name', 'members': []},
            patch_body={'name': 'New Name'},
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read and write permissions."""

        self.client.force_authenticate(user=self.team_owner)
        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={'name': 'New Name', 'members': []},
            patch_body={'name': 'New Name'},
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have read and write permissions."""

        self.client.force_authenticate(user=self.staff_user)
        self.assert_http_responses(
            self.team_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={'name': 'New Name', 'members': []},
            patch_body={'name': 'New Name'},
        )


class SlugHandling(APITestCase):
    """Test slug value handling on team updates."""

    endpoint_pattern = ENDPOINT_PATTERN

    def setUp(self) -> None:
        """Authenticate a team owner."""

        self.team = TeamFactory(name="Original Name")
        self.owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user
        self.client.force_authenticate(user=self.owner)
        self.endpoint = self.endpoint_pattern.format(pk=self.team.pk)

    def test_slug_updates_when_name_changes(self) -> None:
        """Verify the slug value is automatically updated when the team name changes."""

        response = self.client.patch(self.endpoint, {"name": "Renamed Team"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.team.refresh_from_db()
        self.assertEqual("renamed-team", self.team.slug)

    def test_slug_not_overridden_manually(self) -> None:
        """Verify manually specified slug values are ignored during update."""

        response = self.client.patch(self.endpoint, {"name": "Another Name", "slug": "wrong-slug"})

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.team.refresh_from_db()
        self.assertNotEqual("wrong-slug", self.team.slug)
        self.assertEqual("another-name", self.team.slug)

    def test_slug_unchanged_if_name_unchanged(self) -> None:
        """Verify slug values remain unchanged if the name is not modified."""

        original_slug = self.team.slug
        response = self.client.patch(self.endpoint, {"membership": []})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.team.refresh_from_db()
        self.assertEqual(original_slug, self.team.slug)

    def test_slug_uniqueness_enforced(self) -> None:
        """Verify slug uniqueness is enforced when updating records."""

        # Create two initial team records
        TeamFactory(name="Team 1")
        TeamFactory(name="Team 2")
        endpoint2 = self.endpoint_pattern.format(pk=1)

        # Rename second team so the name renames unique but the slug conflicts with the first team
        response1 = self.client.patch(endpoint2, {"name": "Team-1"})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response1.status_code)
