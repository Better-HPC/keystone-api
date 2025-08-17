"""Custom testing utilities used to streamline common tests."""

from abc import ABC, abstractmethod
from typing import TypeVar

from django.db import transaction
from factory.django import DjangoModelFactory
from rest_framework.test import APITestCase

from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership, Team, User

TApiTestCase = TypeVar("TApiTestCase", bound=APITestCase)


class CustomAsserts:
    """Custom assert methods for testing responses from REST endpoints."""

    def assert_http_responses(self: TApiTestCase, endpoint: str, **kwargs) -> None:
        """Execute a series of API calls and assert the returned status matches the given values.

        Args:
            endpoint: The partial URL endpoint to perform requests against.
            **<request>: The integer status code expected by the given request type (get, post, etc.).
            **<request>_body: The data to include in the request (get_body, post_body, etc.).
            **<request>_headers: Header values to include in the request (get_headers, post_headers, etc.).
        """

        http_methods = ['get', 'head', 'options', 'post', 'put', 'patch', 'delete', 'trace']
        for method in http_methods:
            expected_status = kwargs.get(method, None)
            if expected_status is not None:
                self._assert_http_response(method, endpoint, expected_status, kwargs)

    def _assert_http_response(self: TApiTestCase, method: str, endpoint: str, expected_status: int, kwargs: dict):
        """Assert the HTTP response for a specific method matches the expected status.

        Args:
            method: The HTTP method to use (get, post, etc.).
            endpoint: The partial URL endpoint to perform requests against.
            expected_status: The integer status code expected by the given request type.
            kwargs: Additional keyword arguments for building the request.
        """

        http_callable = getattr(self.client, method)
        http_args = self._build_request_args(method, kwargs)

        # Preserve database state
        with transaction.atomic():
            request = http_callable(endpoint, **http_args)
            self.assertEqual(
                request.status_code, expected_status,
                f'{method.upper()} request received {request.status_code} instead of {expected_status} with content "{request.content}"')

            transaction.set_rollback(True)

    @staticmethod
    def _build_request_args(method: str, kwargs: dict) -> dict:
        """Isolate head and body arguments for a given HTTP method from a dict of arguments.

        Args:
            method: The HTTP method to identify arguments for.
            kwargs: A dictionary of arguments.

        Returns:
            A dictionary containing formatted arguments.
        """

        arg_names = ('data', 'headers')
        arg_values = (kwargs.get(f'{method}_body', None), kwargs.get(f'{method}_headers', None))
        return {name: value for name, value in zip(arg_names, arg_values) if value is not None}


class TeamScopedListFilteringTestMixin(ABC):
    """Test the filtering of returned records based on user team membership."""

    # Test configuration
    team_field = 'team'

    # Test Fixtures
    team: Team
    team_member: User
    staff_user: User
    generic_user: User
    team_records: list
    all_records: list

    @property
    @abstractmethod
    def factory(self) -> type[DjangoModelFactory]:
        """Object factory used to define valid record data during testing."""

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """The API endpoint to test."""

    def setUp(self: TApiTestCase) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory()
        self.team_member = MembershipFactory(team=self.team, role=Membership.Role.MEMBER).user

        self.generic_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.team_records = [self.factory(**{self.team_field: self.team}) for _ in range(5)]
        self.all_records = [self.factory() for _ in range(5)] + self.team_records

    def test_user_returned_filtered_records(self: TApiTestCase) -> None:
        """Verify users are only returned records for teams they belong to."""

        self.client.force_authenticate(self.team_member)

        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = {record.id for record in self.team_records}
        self.assertSetEqual(expected_ids, response_ids)

    def test_staff_returned_all_records(self: TApiTestCase) -> None:
        """Verify staff users are returned all records."""

        self.client.force_authenticate(self.staff_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = {record.id for record in self.all_records}
        self.assertSetEqual(expected_ids, response_ids)

    def test_user_with_no_records(self: TApiTestCase) -> None:
        """Verify user's not belonging to any teams are returned an empty list."""

        self.client.force_authenticate(self.generic_user)
        response = self.client.get(self.endpoint)

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json()))


class UserScopedListFilteringTestMixin:
    """Test the filtering of returned records based on user ownership."""

    # Test configuration
    user_field = 'user'

    # Test Fixtures
    owner_user: User
    other_user: User
    staff_user: User
    user_records: list
    all_records: list

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """The API endpoint to test."""

    @property
    @abstractmethod
    def factory(self) -> type[DjangoModelFactory]:
        """Object factory used to define valid record data during testing."""

    def setUp(self: TApiTestCase) -> None:
        """Create test fixtures using mock data."""

        self.owner_user = UserFactory()
        self.other_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

        self.user_records = [self.factory(**{self.user_field: self.owner_user}), ]
        self.all_records = [self.factory() for _ in range(5)] + self.user_records

    def test_user_returned_own_records(self: TApiTestCase) -> None:
        """Verify users only receive records they own."""

        self.client.force_authenticate(self.owner_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = {record.id for record in self.user_records}
        self.assertSetEqual(expected_ids, response_ids)

    def test_staff_returned_all_records(self: TApiTestCase) -> None:
        """Verify staff users are returned all records."""

        self.client.force_authenticate(self.staff_user)

        response = self.client.get(self.endpoint)
        self.assertEqual(200, response.status_code)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = {record.id for record in self.all_records}
        self.assertSetEqual(expected_ids, response_ids)

    def test_user_with_no_records(self: TApiTestCase) -> None:
        """Verify users with no associated records receive an empty list."""

        self.client.force_authenticate(self.other_user)
        response = self.client.get(self.endpoint)

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.json()))
