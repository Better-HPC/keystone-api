"""Function tests for the `/allocations/clusters/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.factories import ClusterFactory
from apps.allocations.models import Cluster
from apps.users.factories import MembershipFactory, UserFactory
from tests.utils import CustomAsserts

ENDPOINT = '/allocations/clusters/'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User         | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        ClusterFactory()
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
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
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
            post_body={'name': 'foo', 'api_url': 'localhost:6820', 'api_user': 'slurm', 'api_token': 'foobar'}
        )


class ClusterAccessLists(APITestCase):
    """Test returned cluster records are filtered by access white/black lists."""

    endpoint = ENDPOINT

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        membership = MembershipFactory()
        self.generic_user = membership.user
        self.team = membership.team

        # Create cluster records with various access modes
        self.open_cluster = ClusterFactory(access_mode=Cluster.AccessChoices.OPEN)
        self.whitelist_cluster = ClusterFactory(access_mode=Cluster.AccessChoices.WHITELIST)
        self.blacklist_cluster = ClusterFactory(access_mode=Cluster.AccessChoices.BLACKLIST)

        # Tie regulated clusters to team access lists
        self.whitelist_cluster.access_teams.add(self.team)
        self.blacklist_cluster.access_teams.add(self.team)

    def test_access_lists_enforced(self) -> None:
        """Verify returned cluster records are regulated by white/black lists."""

        self.client.force_authenticate(user=self.generic_user)

        response = self.client.get(self.endpoint)
        returned_ids = set(record['id'] for record in response.data['results'])

        expected_ids = {self.open_cluster.id, self.whitelist_cluster.id}

        # Should return the open and team whitelisted clusters but not the blacklisted cluster
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertSetEqual(expected_ids, returned_ids)
        self.assertNotIn(self.blacklist_cluster.id, returned_ids)
