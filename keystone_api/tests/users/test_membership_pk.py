"""Function tests for the `/users/membership/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member (other record) | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member (own record)   | 200 | 200  | 200     | 405  | 403 | 403   | 204    | 405   |
    | Team admin                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Team owner                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = '/users/membership/{pk}/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership = MembershipFactory(role=Membership.Role.MEMBER)
        self.team = membership.team

        self.team_member1 = membership.user
        self.team_member2 = MembershipFactory(team=membership.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=membership.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=membership.team, role=Membership.Role.OWNER).user

        self.non_team_member = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

        self.member1_endpoint = self.endpoint_pattern.format(pk=membership.pk)

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        self.assert_http_responses(
            self.member1_endpoint,
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
            self.member1_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_team_member_own_record_permissions(self) -> None:
        """Verify team members have read and delete permissions for their own record."""

        self.client.force_authenticate(user=self.team_member1)
        self.assert_http_responses(
            self.member1_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_team_member_others_record_permissions(self) -> None:
        """Verify team members have read-only permissions for other team member's records."""

        self.client.force_authenticate(user=self.team_member2)
        self.assert_http_responses(
            self.member1_endpoint,
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
        """Verify team admins have read and write permissions for their own record."""

        self.client.force_authenticate(user=self.team_admin)
        self.assert_http_responses(
            self.member1_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={
                'user': self.non_team_member.pk,
                'team': self.team.pk,
                'role': Membership.Role.MEMBER
            }
        )

    def test_team_owner_permissions(self) -> None:
        """Verify team owners have read and write permissions for their own record."""

        self.client.force_authenticate(user=self.team_owner)
        self.assert_http_responses(
            self.member1_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={
                'user': self.non_team_member.pk,
                'team': self.team.pk,
                'role': Membership.Role.MEMBER
            }
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        self.client.force_authenticate(user=self.staff_user)
        self.assert_http_responses(
            self.member1_endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={
                'user': self.non_team_member.pk,
                'team': self.team.pk,
                'role': Membership.Role.MEMBER
            }
        )
