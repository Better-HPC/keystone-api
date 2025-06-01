"""Common tests for research endpoints."""

from abc import ABC, abstractmethod
from typing import Type

from rest_framework import status

from apps.users.models import Team, User
from tests.utils import CustomAsserts


class ListEndpointPermissionsTests(ABC, CustomAsserts):
    """Test user permissions for list endpoints.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team Member                | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team Admin                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team Owner                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint: str = None  # To be defined by subclass

    # Test Fixtures
    team: Team
    team_member: User
    team_admin: User
    team_owner: User
    staff_user: User
    generic_user: User
    valid_record_data: dict

    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and test fixtures."""

        self.team = Team.objects.get(name='Team 1')
        self.team_member = User.objects.get(username='member_1')
        self.team_admin = User.objects.get(username='admin_1')
        self.team_owner = User.objects.get(username='owner_1')

        self.generic_user = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

        self.valid_record_data = self.build_valid_record_data()

    @abstractmethod
    def build_valid_record_data(self) -> dict:
        """Override to return valid record data for the tested resource.

        Returns:
            A dictionary of valid record data.
        """

        raise NotImplementedError

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
        """Verify users have read access but cannot create records for teams where they are not members."""

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
            post_body=self.valid_record_data
        )

    def test_team_member_permissions(self) -> None:
        """Verify regular team members have read-only access."""

        self.client.force_authenticate(user=self.team_member)
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
            post_body=self.valid_record_data
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
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body=self.valid_record_data
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
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body=self.valid_record_data
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
            post_body=self.valid_record_data
        )


class RecordEndpointPermissionsTests(CustomAsserts):
    """Test user permissions for per-record endpoints.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 403 | 403  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Team Member                | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    | Staff User                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    # To be defined by subclass
    model: Type
    endpoint_pattern: str

    # Test Fixtures
    team: Team
    team_member: User
    non_member: User
    staff_user: User
    valid_record_data: dict

    endpoint: str
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and data from test fixtures."""

        self.team = Team.objects.get(name='Team 1')
        record = self.model.objects.filter(team=self.team).first()
        self.endpoint = self.endpoint_pattern.format(pk=record.pk)

        self.team_member = User.objects.get(username='member_1')
        self.non_member = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

        self.valid_record_data = self.build_valid_record_data()

    def build_valid_record_data(self) -> dict:
        """Override to return valid record data for the tested resource.

        Returns:
            A dictionary of valid record data.
        """

        raise NotImplementedError

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
        """Verify team members have read and write permissions against their own group records."""

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
            put_body=self.valid_record_data,
            patch_body=self.valid_record_data
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
            put_body=self.valid_record_data,
            patch_body=self.valid_record_data
        )
