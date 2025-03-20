"""Function tests for the `/research/publications/<pk>/` endpoint."""

import datetime

from rest_framework import status
from rest_framework.test import APITestCase

from apps.research_products.models import Publication
from apps.users.models import Team, User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    | Authenticated non-member   | 404 | 404  | 200     | 405  | 404 | 404   | 404    | 403   |
    | Team Member                | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 403   |
    | Staff User                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = '/research/publications/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts and allocation data from test fixtures."""

        # Load a team of users and define an allocation endpoint belonging to that team
        self.team = Team.objects.get(name='Team 1')
        self.publication = Publication.objects.filter(team=self.team).first()
        self.endpoint = self.endpoint_pattern.format(pk=self.publication.pk)

        # Load (non)member accounts for the team
        self.staff_user = User.objects.get(username='staff_user')
        self.non_member = User.objects.get(username='generic_user')
        self.team_member = User.objects.get(username='member_1')

        self.valid_record_data = {
            'title': 'foo',
            'abstract': 'bar',
            'journal': 'baz',
            'date': datetime.date(1990, 1, 1),
            'team': self.team.name}

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

    def test_non_member_permissions(self) -> None:
        """Verify users cannot access records for a team they are not in."""

        self.client.force_authenticate(user=self.non_member)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_404_NOT_FOUND,
            head=status.HTTP_404_NOT_FOUND,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_404_NOT_FOUND,
            patch=status.HTTP_404_NOT_FOUND,
            delete=status.HTTP_404_NOT_FOUND,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_team_member_permissions(self) -> None:
        """Verify users can access records owned by a team they are on."""

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
            trace=status.HTTP_403_FORBIDDEN,
            put_body=self.valid_record_data,
        )

    def test_staff_user_permissions(self) -> None:
        """verify staff users have full read and write permissions."""

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
