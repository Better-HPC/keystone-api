"""Function tests for the `batch:job` endpoint."""

import io
import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.allocations.factories import AllocationRequestFactory
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
            content_type='application/json',
            get=status.HTTP_405_METHOD_NOT_ALLOWED,
            head=status.HTTP_405_METHOD_NOT_ALLOWED,
            options=status.HTTP_200_OK,
            post=status.HTTP_200_OK,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={'job': {'actions': [{
                'method': 'GET',
                'path': '/authentication/whoami/',
            }]}},
        )


class RefTokenResolution(APITestCase):
    """Test that `@ref` tokens in paths and payloads are resolved across job steps."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_ref_token_in_path_is_resolved(self) -> None:
        """Verify an `@ref` token in a later step's path is resolved from an earlier step's response."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/authentication/whoami/', 'ref': 'whoami'},
                {'method': 'GET', 'path': '/users/users/@ref{whoami.id}/'},
            ]}},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)

        results = response.json()['results']
        self.assertEqual(2, len(results))

        # Verify the second step resolved @ref{whoami.id} into a concrete user path
        whoami_id = results[0]['body']['id']
        self.assertIn(str(whoami_id), results[1]['path'])

    def test_ref_token_in_body_is_resolved(self) -> None:
        """Verify an `@ref` token in a later step's payload is resolved from an earlier step's response."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/authentication/whoami/', 'ref': 'whoami'},
                {'method': 'PATCH', 'path': '/users/users/@ref{whoami.id}/', 'payload': {
                    'role': '@ref{whoami.username}'
                }},
            ]}},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)

        results = response.json()['results']
        self.assertEqual(2, len(results))

        # Verify the patched role value matches the username resolved from the first step
        whoami_username = results[0]['body']['username']
        self.assertEqual(whoami_username, results[1]['body']['role'])

    def test_duplicate_ref_aliases_return_400(self) -> None:
        """Verify submitting two steps with identical ref aliases returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/api/a/', 'ref': 'step_one'},
                {'method': 'GET', 'path': '/api/b/', 'ref': 'step_one'},
            ]}},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'actions': ['Reference aliases must be unique within a job.']}, response.json())

    def test_non_alphanumeric_ref_alias_returns_400(self) -> None:
        """Verify a ref alias containing special characters returns a 400 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [{'method': 'GET', 'path': '/api/a/', 'ref': 'bad-alias!'}]}},
        )

        expected_error = {'actions': [
            {'ref': ['Reference aliases may only contain alphanumeric characters and underscores.']}
        ]}

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(expected_error, response.json())

    def test_unresolvable_ref_token_returns_422(self) -> None:
        """Verify an `@ref` token pointing to an undefined alias returns a 422 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/api/items/@ref{missing.id}/'},
            ]}},
        )

        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, response.status_code)

        payload = response.json()
        self.assertIn('token', payload)
        self.assertEqual('@ref{missing.id}', payload['token'])

        self.assertIn('detail', payload)
        self.assertIn('Alias "missing" has not been defined by a previous step', payload['detail'])

    def test_non_alphanumeric_ref_token_label_returns_422(self) -> None:
        """Verify an `@ref` token whose label contains invalid characters returns a 422 error."""

        # Label validation happens inside _resolve_token at execution time, not
        # at serialization time, so an invalid label produces a 422 rather than a 400.
        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/api/items/@ref{bad-label!.id}/'},
            ]}},
        )

        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, response.status_code)

        payload = response.json()
        self.assertIn('token', payload)
        self.assertEqual('@ref{bad-label!.id}', payload['token'])

        self.assertIn('detail', payload)
        self.assertIn(' Reference labels may only contain letters, numbers, and underscores', payload['detail'])


class FileTokenResolution(APITestCase):
    """Test job execution when steps reference uploaded files via `@file` tokens."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user = UserFactory(is_staff=True)
        self.alloc_request = AllocationRequestFactory(submitter=self.user)
        self.client.force_authenticate(user=self.user)

    def test_file_token_in_payload_is_resolved(self) -> None:
        """Verify a step whose payload contains a `@file` token receives the uploaded file."""

        upload = io.BytesIO(b'hello world')
        upload.name = 'hello.txt'

        response = self.client.post(
            self.endpoint,
            data={
                'job': json.dumps({'actions': [{
                    'method': 'POST',
                    'path': '/allocations/attachments/',
                    'payload': {
                        'file': '@file{doc}',
                        'request': self.alloc_request.pk
                    },
                }]}),
                'doc': upload,
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)

    def test_unresolvable_file_token_returns_422(self) -> None:
        """Verify a `@file` token with no matching uploaded file returns a 422 error."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [{
                'method': 'POST',
                'path': '/allocations/attachments/',
                'payload': {
                    'file': '@file{doc}',
                    'request': self.alloc_request.pk
                },
            }]}},
        )

        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, response.status_code)

        payload = response.json()
        self.assertIn('token', payload)
        self.assertEqual('@file{doc}', payload['token'])

        self.assertIn('detail', payload)
        self.assertIn('File part "doc" was not uploaded with this request', payload['detail'])

    def test_non_alphanumeric_file_token_label_returns_422(self) -> None:
        """Verify a `@file` token whose label contains invalid characters returns a 422 error."""

        upload = io.BytesIO(b'hello world')
        upload.name = 'hello.txt'

        response = self.client.post(
            self.endpoint,
            data={
                'job': json.dumps({'actions': [{
                    'method': 'POST',
                    'path': '/allocations/attachments/',
                    'payload': {
                        'file': '@file{bad-label!}',
                        'request': self.alloc_request.pk
                    },
                }]}),
                'bad-label!': upload,
            },
        )

        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, response.status_code)

        payload = response.json()
        self.assertIn('token', payload)
        self.assertEqual('@file{bad-label!}', payload['token'])

        self.assertIn('detail', payload)
        self.assertIn(' Reference labels may only contain letters, numbers, and underscores', payload['detail'])


class JobExecution(APITestCase):
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
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/authentication/whoami/', 'ref': 'whoami'},
                {'method': 'GET', 'path': '/users/users/@ref{whoami.id}/'},
            ]}},
        )

        # Verify returned 200 response includes results
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        self.assertEqual(2, len(response.json()['results']))

        # Verify results from a user query include the correct user data
        current_username = self.user.username
        returned_username = response.json()['results'][1]['body']['username']
        self.assertEqual(current_username, returned_username)

    def test_step_failure_returns_422(self) -> None:
        """Verify a job that raises JobExecutionError returns a 422."""

        response = self.client.post(
            self.endpoint,
            content_type='application/json',
            data={'job': {'actions': [
                {'method': 'GET', 'path': '/fake/endpoint/'},
            ]}},
        )

        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, response.status_code)

        payload = response.json()
        self.assertIn('detail', payload)
        self.assertIn('step', payload)
        self.assertIn('status', payload)
        self.assertIn('body', payload)
        self.assertEqual(1, payload['step'])
        self.assertEqual(404, payload['status'])
