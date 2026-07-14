"""Function tests for the `allocations:allocation-list` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.factories import AllocationRequestFactory, ClusterFactory, ResourceAllocationFactory
from apps.allocations.models import Cluster, ResourceAllocation
from apps.users.factories import MembershipFactory, UserFactory
from apps.users.models import Membership
from tests.function_tests.utils import CustomAsserts, TeamListFilteringTestMixin

VIEW_NAME = "allocations:allocation-list"


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.
    Permissions depend on the user's role within the team owning the accessed record.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated non-member   | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team member                | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Team admin                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Team owner                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    | Staff User                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.allocation = ResourceAllocationFactory()

        self.team = self.allocation.request.team
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.team_owner = MembershipFactory(team=self.team, role=Membership.Role.OWNER).user

        self.non_member = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.valid_record_data = {
            "requested": 1000,
            "cluster": self.allocation.cluster.pk,
            "request": self.allocation.request.pk,
        }

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
            trace=status.HTTP_401_UNAUTHORIZED,
        )

    def test_non_team_member_permissions(self) -> None:
        """Verify authenticated non-members have read-only access."""

        self.client.force_authenticate(user=self.non_member)
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
            post_body=self.valid_record_data,
        )

    def test_team_member_permissions(self) -> None:
        """Verify team members have read-only access."""

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
            post_body=self.valid_record_data,
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
            post_body=self.valid_record_data,
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
            post_body=self.valid_record_data,
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
            post_body=self.valid_record_data,
        )


class ClusterAccessPermissions(APITestCase):
    """Test allocation creation is restricted by each cluster's access mode.

    Non-staff users may only create allocations on clusters their team is
    permitted to use under the cluster's access mode. Staff users are exempt
    from the cluster access policy. All scenarios use a team administrator so
    that creation is gated solely by cluster access rather than team role.
    """

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.request = AllocationRequestFactory()
        self.team = self.request.team
        self.team_admin = MembershipFactory(team=self.team, role=Membership.Role.ADMIN).user
        self.staff_user = UserFactory(is_staff=True)

    def build_post_body(self, cluster: Cluster) -> dict:
        """Return valid allocation creation data targeting the given cluster."""

        return {"requested": 1000, "cluster": cluster.pk, "request": self.request.pk}

    def test_open_cluster_allows_creation(self) -> None:
        """Verify team admins can create allocations on open clusters."""

        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.OPEN)

        self.client.force_authenticate(user=self.team_admin)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

    def test_whitelisted_team_allows_creation(self) -> None:
        """Verify team admins can create allocations on clusters whitelisting their team."""

        # Whitelist the requesting team on the target cluster
        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.WHITELIST)
        cluster.access_teams.add(self.team)

        self.client.force_authenticate(user=self.team_admin)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

    def test_non_whitelisted_team_is_denied_creation(self) -> None:
        """Verify a whitelist cluster produces no allocation for an unlisted team."""

        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.WHITELIST)

        self.client.force_authenticate(user=self.team_admin)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code, response.data)
        self.assertFalse(
            ResourceAllocation.objects.filter(cluster=cluster).exists(),
            "Allocation was created on a cluster the team is not whitelisted for"
        )

    def test_blacklisted_team_is_denied_creation(self) -> None:
        """Verify a blacklist cluster produces no allocation for a listed team."""

        # Blacklist the requesting team on the target cluster
        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.BLACKLIST)
        cluster.access_teams.add(self.team)

        self.client.force_authenticate(user=self.team_admin)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code, response.data)
        self.assertFalse(
            ResourceAllocation.objects.filter(cluster=cluster).exists(),
            "Allocation was created on a cluster the team is blacklisted from"
        )

    def test_non_blacklisted_team_allows_creation(self) -> None:
        """Verify team admins can create allocations on blacklist clusters that omit their team."""

        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.BLACKLIST)

        self.client.force_authenticate(user=self.team_admin)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)

    def test_staff_bypass_cluster_restrictions(self) -> None:
        """Verify staff users can create allocations regardless of cluster access mode."""

        # A whitelist cluster the staff user's context has no team access to
        cluster = ClusterFactory(access_mode=Cluster.AccessModeChoices.WHITELIST)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.endpoint, self.build_post_body(cluster))

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)


class TeamRecordFiltering(TeamListFilteringTestMixin, APITestCase):
    """Test the filtering of returned records based on user team membership."""

    endpoint = reverse(VIEW_NAME)
    factory = ResourceAllocationFactory
    team_field = "request__team"
