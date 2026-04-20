"""Function tests for the `batch:job` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from tests.function_tests.utils import CustomAsserts

VIEW_NAME = 'batch:batch'


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status          | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated User | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated User   | 405 | 405  | 200     | 200  | 405 | 405   | 405    | 405   |
    """

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory()

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

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users can only POST to this endpoint."""

        self.client.force_authenticate(user=self.user)
        self.assert_http_responses(
            self.endpoint,
            content_type="application/json",
            get=status.HTTP_405_METHOD_NOT_ALLOWED,
            head=status.HTTP_405_METHOD_NOT_ALLOWED,
            options=status.HTTP_200_OK,
            post=status.HTTP_200_OK,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'actions': [{
                'method': 'GET',
                'path': '/authentication/whoami/',
            }]},
        )


class PostRequestValidation(APITestCase):
    """Test input validation for POST requests."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_missing_actions_field_returns_400(self) -> None:
        """Verify submitting a payload without an `actions` field returns a 400 error."""

        response = self.client.post(self.endpoint, data={}, content_type='application/json')
        expected_error = {'actions': ['This field is required.']}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_empty_actions_list_returns_400(self) -> None:
        """Verify submitting an empty `actions` list returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': []},
        )

        expected_error = {'actions': {'non_field_errors': ['This list may not be empty.']}}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_invalid_http_method_in_step_returns_400(self) -> None:
        """Verify a step with an unrecognized HTTP method returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': [{'method': 'BREW', 'path': '/api/some-path/'}]},
        )

        expected_error = {'actions': [{'method': ['"BREW" is not a valid choice.']}]}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_missing_method_in_step_returns_400(self) -> None:
        """Verify a step missing the `method` field returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': [{'path': '/api/some-path/'}]},
        )

        expected_error = {'actions': [{'method': ['This field is required.']}]}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_missing_path_in_step_returns_400(self) -> None:
        """Verify a step missing the `path` field returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': [{'method': 'GET'}]},
        )

        expected_error = {'actions': [{'path': ['This field is required.']}]}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_duplicate_ref_aliases_return_400(self) -> None:
        """Verify submitting two steps with identical ref aliases returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={
                'actions': [
                    {'method': 'GET', 'path': '/api/a/', 'ref': 'step_one'},
                    {'method': 'GET', 'path': '/api/b/', 'ref': 'step_one'},
                ]
            },
        )

        expected_error = {'actions': ['Reference aliases must be unique within a job.']}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())

    def test_non_alphanumeric_ref_alias_returns_400(self) -> None:
        """Verify a ref alias containing special characters returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': [{'method': 'GET', 'path': '/api/a/', 'ref': 'bad-alias!'}]},
        )

        expected_error = {'actions': [
            {'ref': ['Reference aliases may only contain alphanumeric characters and underscores.']}
        ]}

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expected_error, response.json())


class SuccessfulJobExecution(APITestCase):
    """Test the response shape for a successfully completed job."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_successful_job_returns_200(self) -> None:
        """Verify a job whose steps all succeed returns a 200 with results."""

        response = self.client.post(
            self.endpoint,
            content_type="application/json",
            data={
                'actions': [
                    {'method': 'GET', 'path': '/authentication/whoami/', 'ref': 'whoami'},
                    {'method': 'GET', 'path': '/users/users/@ref{whoami.id}/'},
                ]
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        self.assertEqual(len(response.json()['results']), 2)


class FailedJobExecution(APITestCase):
    """Test the response shape when a job step fails during execution."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_step_failure_returns_422(self) -> None:
        """Verify a job that raises JobExecutionError returns a 422."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={
                'actions': [
                    {'method': 'GET', 'path': '/fake/endpoint/'},
                ]
            },
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        payload = response.json()
        self.assertIn('detail', payload)
        self.assertIn('step', payload)
        self.assertIn('status', payload)
        self.assertIn('body', payload)
        self.assertEqual(payload['step'], 1)
        self.assertEqual(payload['status'], 404)

    def test_reference_resolution_failure_returns_422(self) -> None:
        """Verify a job that raises ReferenceResolutionError returns a 422."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'actions': [{'method': 'GET', 'path': '/api/items/@ref{missing.id}/'}]},
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        payload = response.json()
        self.assertIn('detail', payload)
        self.assertIn('token', payload)
        self.assertEqual(payload['token'], '@ref{missing.id}')
