"""Function tests for the `users:team-detail` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership
from tests.function_tests.utils import CustomAsserts

VIEW_NAME = "users:team-detail"


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status              | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |--------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user     | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member              | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team admin               | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Team owner               | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Staff user               | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory(is_active=True)
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user

        self.non_team_member = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.endpoint = reverse(VIEW_NAME, kwargs={"pk": self.team.id})

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

    def test_non_member_permissions(self) -> None:
        """Verify non-members have read-only permissions."""

        self.client.force_authenticate(user=self.non_team_member)
        self.assert_http_responses(
            self.endpoint,
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
            self.endpoint,
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
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={"is_active": False},
            patch_body={"is_active": False},
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read and write permissions."""

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
            put_body={"is_active": False},
            patch_body={"is_active": False},
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have read and write permissions."""

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
            put_body={"is_active": False},
            patch_body={"is_active": False},
        )


class NameHandling(APITestCase):
    """Test the `name` field is readonly for update operations."""

    def setUp(self) -> None:
        """Authenticate as a team owner."""

        self.team = TeamFactory(name="Original Name")
        self.staff_user = UserFactory(is_staff=True)

        self.client.force_authenticate(user=self.staff_user)
        self.endpoint = reverse(VIEW_NAME, kwargs={"pk": self.team.id})

    def test_name_is_read_only_on_put(self) -> None:
        """Verify the team name cannot be modified via a full update."""

        original_name = self.team.name
        original_slug = self.team.slug
        self.client.put(self.endpoint, {"name": "New Name", "is_active": True})

        self.team.refresh_from_db()
        self.assertEqual(original_name, self.team.name)
        self.assertEqual(original_slug, self.team.slug)

    def test_name_is_read_only_on_patch(self) -> None:
        """Verify the team name cannot be patched after creation."""

        original_name = self.team.name
        original_slug = self.team.slug
        self.client.force_authenticate(user=self.staff_user)
        self.client.patch(self.endpoint, {"name": "New Name"})

        self.team.refresh_from_db()
        self.assertEqual(original_name, self.team.name)
        self.assertEqual(original_slug, self.team.slug)


class InactiveTeamAccess(APITestCase):
    """Test access to inactive team records."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.inactive_team = TeamFactory(is_active=False)
        self.team_member = MembershipFactory(team=self.inactive_team, role=Membership.Role.MEMBER).user
        self.staff_user = UserFactory(is_staff=True)
        self.endpoint = reverse(VIEW_NAME, kwargs={"pk": self.inactive_team.id})

    def test_staff_can_retrieve_inactive_team(self) -> None:
        """Verify staff users can retrieve inactive team records."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.endpoint)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_staff_can_modify_inactive_team(self) -> None:
        """Verify staff users can modify inactive team records."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(self.endpoint, {"is_active": True})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_staff_can_delete_inactive_team(self) -> None:
        """Verify staff users can delete inactive team records."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(self.endpoint)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_non_staff_cannot_retrieve_inactive_team(self) -> None:
        """Verify non-staff users cannot retrieve inactive team records."""

        self.client.force_authenticate(user=self.team_member)
        response = self.client.get(self.endpoint)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_non_staff_cannot_modify_inactive_team(self) -> None:
        """Verify non-staff users cannot modify inactive team records."""

        self.client.force_authenticate(user=self.team_member)
        response = self.client.patch(self.endpoint, {"is_active": True})
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_non_staff_cannot_delete_inactive_team(self) -> None:
        """Verify non-staff users cannot delete inactive team records."""

        self.client.force_authenticate(user=self.team_member)
        response = self.client.delete(self.endpoint)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
