"""Custom testing utilities used to streamline common tests."""

from django.db import transaction
from django.db.models import Model, QuerySet
from django.test import Client

from apps.users.models import Team, User


class CustomAsserts:
    """Custom assert methods for testing responses from REST endpoints."""

    client: Client
    assertEqual: callable  # Provided by TestCase class

    def assert_http_responses(self, endpoint: str, **kwargs) -> None:
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

    def _assert_http_response(self, method: str, endpoint: str, expected_status: int, kwargs: dict):
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
            A dictionary with formatted arguments.
        """

        arg_names = ('data', 'headers')
        arg_values = (kwargs.get(f'{method}_body', None), kwargs.get(f'{method}_headers', None))
        return {name: value for name, value in zip(arg_names, arg_values) if value is not None}


class TeamScopedListFilteringTests:
    """Test the filtering of returned records based on user team membership."""

    # Defined by subclasses
    model: Model
    endpoint: str
    team_field = 'team'

    # Test Fixtures
    team: Team
    team_member: User
    staff_user: User
    generic_user: User
    team_records: QuerySet
    all_records: QuerySet

    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load records from test fixtures."""

        self.team = Team.objects.get(name='Team 1')
        self.team_records = self.model.objects.filter(**{self.team_field: self.team})
        self.all_records = self.model.objects.all()

        self.team_member = User.objects.get(username='member_1')
        self.generic_user = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

    def test_user_returned_filtered_records(self) -> None:
        """Verify users are only returned records for teams they belong to."""

        self.client.force_login(self.team_member)
        response = self.client.get(self.endpoint)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = set(self.team_records.values_list('id', flat=True))
        self.assertSetEqual(expected_ids, response_ids)

    def test_staff_returned_all_records(self) -> None:
        """Verify staff users are returned all records."""

        self.client.force_login(self.staff_user)
        response = self.client.get(self.endpoint)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = set(self.all_records.values_list('id', flat=True))
        self.assertSetEqual(expected_ids, response_ids)

    def test_user_with_no_records(self) -> None:
        """Verify user's not belonging to any teams are returned an empty list."""

        self.client.force_login(self.generic_user)
        response = self.client.get(self.endpoint)
        self.assertEqual(0, len(response.json()))


class UserScopedListFilteringTests:
    """Test the filtering of returned records based on user ownership."""

    # Defined by subclasses
    model: Model
    endpoint: str
    user_field = 'user'

    # Test Fixtures
    owner_user: User
    other_user: User
    staff_user: User
    user_records: QuerySet
    all_records: QuerySet

    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load records from test fixtures."""

        self.owner_user = User.objects.get(username='member_1')
        self.other_user = User.objects.get(username='generic_user')
        self.staff_user = User.objects.get(username='staff_user')

        self.user_records = self.model.objects.filter(**{self.user_field: self.owner_user})
        self.all_records = self.model.objects.all()

    def test_user_returned_own_records(self) -> None:
        """Verify users only receive records they own."""

        self.client.force_login(self.owner_user)
        response = self.client.get(self.endpoint)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = set(self.user_records.values_list('id', flat=True))
        self.assertSetEqual(expected_ids, response_ids)

    def test_staff_returned_all_records(self) -> None:
        """Verify staff users are returned all records."""

        self.client.force_login(self.staff_user)
        response = self.client.get(self.endpoint)

        response_ids = {record['id'] for record in response.json()}
        expected_ids = set(self.all_records.values_list('id', flat=True))
        self.assertSetEqual(expected_ids, response_ids)

    def test_user_with_no_records(self) -> None:
        """Verify users with no associated records receive an empty list."""

        self.client.force_login(self.other_user)
        response = self.client.get(self.endpoint)
        self.assertEqual(0, len(response.json()))
