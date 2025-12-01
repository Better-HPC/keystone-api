"""Function tests for the `/allocations/clusters/<pk>/` endpoint."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.factories import ClusterFactory
from apps.allocations.models import Cluster
from apps.users.factories import MembershipFactory, UserFactory
from tests.utils import CustomAsserts

ENDPOINT_PATTERN = '/allocations/clusters/{pk}/'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User         | 200 | 200  | 200     | 405  | 403 | 403   | 403    | 405   |
    | Staff User                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = ENDPOINT_PATTERN

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        cluster = ClusterFactory()
        self.endpoint = self.endpoint_pattern.format(pk=cluster.id)

        self.generic_user = UserFactory()
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

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users have read-only permissions."""

        self.client.force_authenticate(user=self.generic_user)
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
            put_body={'name': 'foo', 'api_url': 'localhost:6820', 'api_user': 'slurm', 'api_token': 'foobar'},
            patch_body={'name': 'foo'}
        )


class ClusterAccessListPermissionIsolationTests(APITestCase):
    """Verify cluster-level access lists do not alter authenticated permission checks."""

    endpoint_pattern = ENDPOINT_PATTERN

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership = MembershipFactory()
        self.user = membership.user
        self.team = membership.team

        # Clusters using access lists
        self.whitelisted = ClusterFactory(access_mode=Cluster.AccessChoices.WHITELIST)
        self.blacklisted = ClusterFactory(access_mode=Cluster.AccessChoices.BLACKLIST)

        # Attach team to both lists
        self.whitelisted.access_teams.add(self.team)
        self.blacklisted.access_teams.add(self.team)

    def test_user_can_access_whitelist_cluster(self) -> None:
        """Verify users can access clusters their team is whitelisted on."""

        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.endpoint_pattern.format(pk=self.whitelisted.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_can_access_blacklist_cluster(self) -> None:
        """Verify users can access clusters their team is blacklisted on."""

        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.endpoint_pattern.format(pk=self.blacklisted.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
