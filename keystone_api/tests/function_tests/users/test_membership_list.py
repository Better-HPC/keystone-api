"""Function tests for the `users:membership-list` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership
from tests.function_tests.utils import CustomAsserts

VIEW_NAME = "users:membership-list"


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status              | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |--------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user     | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team member              | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team admin               | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team owner               | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff user               | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory()
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user

        self.non_team_member = UserFactory()
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

    def test_non_member_permissions(self) -> None:
        """Verify non-members have read-only permissions."""

        self.client.force_authenticate(user=self.non_team_member)
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
            post_body={
                "team": self.team.pk,
                "user": self.non_team_member.pk,
                "role": Membership.Role.MEMBER
            }
        )

    def test_team_member_permissions(self) -> None:
        """Verify team members have read-only permissions."""

        self.client.force_authenticate(user=self.team_member)
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
            post_body={
                "team": self.team.pk,
                "user": self.non_team_member.pk,
                "role": Membership.Role.MEMBER
            }
        )

    def test_team_admin_permissions(self) -> None:
        """Verify team admins have read and write permissions for their own team."""

        self.client.force_authenticate(user=self.team_admin)
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
            post_body={
                "team": self.team.pk,
                "user": self.non_team_member.pk,
                "role": Membership.Role.MEMBER
            }
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read and write permissions for their own team."""

        self.client.force_authenticate(user=self.team_owner)
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
            post_body={
                "team": self.team.pk,
                "user": self.non_team_member.pk,
                "role": Membership.Role.MEMBER
            }
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
            post_body={
                "team": self.team.pk,
                "user": self.non_team_member.pk,
                "role": Membership.Role.MEMBER
            }
        )


class InactiveTeamFiltering(APITestCase):
    """Test filtering of memberships belonging to inactive teams from list results."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        active_team = TeamFactory(is_active=True)
        inactive_team = TeamFactory(is_active=False)
        self.active_membership = MembershipFactory(team=active_team, role=Membership.Role.MEMBER)
        self.inactive_membership = MembershipFactory(team=inactive_team, role=Membership.Role.MEMBER)
        self.staff_user = UserFactory(is_staff=True)
        self.generic_user = UserFactory()

    def test_memberships_for_inactive_teams_hidden_from_non_staff(self) -> None:
        """Verify memberships belonging to inactive teams are not returned to non-staff users."""

        self.client.force_authenticate(user=self.generic_user)
        response = self.client.get(self.endpoint)
        returned_ids = [m["id"] for m in response.data["results"]]
        self.assertNotIn(self.inactive_membership.id, returned_ids)

    def test_non_staff_cannot_create_membership_for_inactive_teams(self) -> None:
        """Verify non-staff users cannot create memberships for inactive teams."""

        inactive_team = TeamFactory(is_active=False)
        admin_user = MembershipFactory(team=inactive_team, role=Membership.Role.ADMIN).user
        new_user = UserFactory()

        self.client.force_authenticate(user=admin_user)
        response = self.client.post(self.endpoint, {
            "team": inactive_team.pk,
            "user": new_user.pk,
            "role": Membership.Role.MEMBER,
        })

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_memberships_for_inactive_teams_visible_to_staff(self) -> None:
        """Verify memberships belonging to inactive teams are returned to staff users."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.endpoint)
        returned_ids = [m["id"] for m in response.data["results"]]
        self.assertIn(self.inactive_membership.id, returned_ids)

    def test_staff_can_create_membership_for_inactive_teams(self) -> None:
        """Verify staff users can create memberships for inactive teams."""

        inactive_team = TeamFactory(is_active=False)
        new_user = UserFactory()

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.endpoint, {
            "team": inactive_team.pk,
            "user": new_user.pk,
            "role": Membership.Role.MEMBER,
        })

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)


class InactiveUserFiltering(APITestCase):
    """Test filtering of memberships belonging to inactive users from list results."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        active_team = TeamFactory(is_active=True)
        self.active_membership = MembershipFactory(team=active_team, role=Membership.Role.MEMBER)
        self.inactive_membership = MembershipFactory(
            team=active_team,
            role=Membership.Role.MEMBER,
            user=UserFactory(is_active=False),
        )
        self.staff_user = UserFactory(is_staff=True)
        self.generic_user = UserFactory()

    def test_memberships_for_inactive_users_hidden_from_non_staff(self) -> None:
        """Verify memberships belonging to inactive users are not returned to non-staff users."""

        self.client.force_authenticate(user=self.generic_user)
        response = self.client.get(self.endpoint)
        returned_ids = [m["id"] for m in response.data["results"]]
        self.assertNotIn(self.inactive_membership.id, returned_ids)

    def test_memberships_for_inactive_users_visible_to_staff(self) -> None:
        """Verify memberships belonging to inactive users are returned to staff users."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.endpoint)
        returned_ids = [m["id"] for m in response.data["results"]]
        self.assertIn(self.inactive_membership.id, returned_ids)
