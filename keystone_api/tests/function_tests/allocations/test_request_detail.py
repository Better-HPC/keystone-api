"""Function tests for the `allocations:request-detail` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.factories import AllocationRequestFactory, CommentFactory
from apps.users.factories import MembershipFactory, UserFactory
from apps.users.models import Membership
from tests.function_tests.utils import CustomAsserts

VIEW_NAME = "allocations:request-detail"


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 403 | 403  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team member                | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team admin                 | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team owner                 | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.request = AllocationRequestFactory()

        self.team = self.request.team
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user

        self.non_member = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.endpoint = reverse(VIEW_NAME, kwargs={'pk': self.request.id})

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
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
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
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
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
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
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


class AllocationCommentsVisibility(APITestCase):
    """Test filtering of nested private comments based on user staff status."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.allocation_request = AllocationRequestFactory()
        self.team = self.allocation_request.team

        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.staff_user = UserFactory(is_staff=True)

        self.public_comment = CommentFactory(
            request=self.allocation_request,
            private=False,
        )

        self.private_comment = CommentFactory(
            request=self.allocation_request,
            private=True,
        )

        self.endpoint = reverse(VIEW_NAME, kwargs={"pk": self.allocation_request.id})

    def _get_comment_ids(self, response) -> set[int]:
        """Extract comment IDs from the response payload."""

        return {comment["id"] for comment in response.data["_comments"]}

    def test_member_sees_only_public_comments(self) -> None:
        """Verify non-staff users only receive non-private comments."""

        self.client.force_authenticate(user=self.team_member)
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = self._get_comment_ids(response)

        self.assertIn(self.public_comment.id, comment_ids)
        self.assertNotIn(self.private_comment.id, comment_ids)

    def test_staff_user_sees_all_comments(self) -> None:
        """Verify staff users receive both public and private comments."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = self._get_comment_ids(response)

        self.assertIn(self.public_comment.id, comment_ids)
        self.assertIn(self.private_comment.id, comment_ids)
