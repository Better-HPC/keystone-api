"""Unit tests for the `execute_job` function."""

from unittest.mock import Mock, patch

from django.test import TestCase

from apps.batch.exceptions import JobExecutionError, ReferenceResolutionError
from apps.batch.shortcuts import execute_job


@patch('apps.batch.shortcuts.execute_step')
class ResultShape(TestCase):
    """Test the structure and content of the result list returned by `execute_job`."""

    def test_returns_one_result_dict_per_step(self, mock_execute_step: Mock) -> None:
        """Verify execute_job returns one result dict per step on success."""

        mock_execute_step.side_effect = [
            (201, {'id': 1}),
            (200, {'id': 2})
        ]
        steps = [
            {'method': 'POST', 'path': '/endpoint1/', 'payload': {'foo': 'x'}},
            {'method': 'GET', 'path': '/endpoint2/', 'payload': {'bar': 'x'}},
        ]

        results = execute_job(steps)

        self.assertEqual(len(results), 2)
        result0, result1 = results

        self.assertEqual(result0['status'], 201)
        self.assertEqual(result0['method'], 'POST')
        self.assertEqual(result0['path'], '/endpoint1/')

        self.assertEqual(result1['status'], 200)
        self.assertEqual(result1['method'], 'GET')
        self.assertEqual(result1['path'], '/endpoint2/')

    def test_step_index_is_one_based(self, mock_execute_step: Mock) -> None:
        """Verify step result indices start at 1, not 0."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'GET', 'path': '/a/'}, {'method': 'GET', 'path': '/b/'}]

        results = execute_job(steps)

        self.assertEqual(results[0]['index'], 1)
        self.assertEqual(results[1]['index'], 2)

    def test_step_without_alias_returns_none(self, mock_execute_step: Mock) -> None:
        """Verify steps without a ref alias record None in the result dict."""

        mock_execute_step.return_value = (200, {'id': 1})
        steps = [{'method': 'GET', 'path': '/endpoint1/'}]

        results = execute_job(steps)

        self.assertIsNone(results[0]['ref'], 'Steps without a ref alias should return None')

    def test_records_ref_alias_in_result(self, mock_execute_step: Mock) -> None:
        """Verify a step's ref alias is recorded in the result dict."""

        mock_execute_step.return_value = (200, {'id': 9})
        steps = [{'ref': 'created', 'method': 'GET', 'path': '/items/9/'}]

        results = execute_job(steps)

        self.assertEqual(results[0]['ref'], 'created')

    def test_empty_steps_list_returns_empty_results(self, mock_execute_step: Mock) -> None:
        """Verify an empty step list produces an empty result list."""

        results = execute_job([])

        mock_execute_step.assert_not_called()
        self.assertEqual(results, [])


@patch('apps.batch.shortcuts.execute_step')
class InputNormalization(TestCase):
    """Test normalization of step fields before dispatch."""

    def test_method_is_uppercased_before_dispatch(self, mock_execute_step: Mock) -> None:
        """Verify a lowercase HTTP method in a step is normalized to uppercase."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'get', 'path': '/items/'}]

        results = execute_job(steps)

        method, *_ = mock_execute_step.call_args_list[0].args
        self.assertEqual(method, 'GET')
        self.assertEqual(results[0]['method'], 'GET')

    def test_step_without_payload_defaults_to_empty_dict(self, mock_execute_step: Mock) -> None:
        """Verify a step omitting `payload` and `query_params` still dispatches successfully."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'GET', 'path': '/items/'}]

        execute_job(steps)

        _method, _path, payload, query_params = mock_execute_step.call_args_list[0].args
        self.assertEqual(payload, {})
        self.assertEqual(query_params, {})


@patch('apps.batch.shortcuts.execute_step')
class ArgumentForwarding(TestCase):
    """Test that caller-supplied arguments are forwarded to each `execute_step` call."""

    def test_passes_user_to_execute_step(self, mock_execute_step: Mock) -> None:
        """Verify the `user` argument is forwarded to `execute_step` on every call."""

        mock_execute_step.return_value = (200, {})
        mock_user = Mock()
        steps = [{'method': 'GET', 'path': '/items/'}]

        execute_job(steps, user=mock_user)

        _, kwargs = mock_execute_step.call_args
        self.assertEqual(kwargs.get('user'), mock_user)

    def test_passes_server_name_to_execute_step(self, mock_execute_step: Mock) -> None:
        """Verify the `server_name` argument is forwarded to `execute_step`."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'GET', 'path': '/items/'}]

        execute_job(steps, server_name='api.example.com')

        _, kwargs = mock_execute_step.call_args
        self.assertEqual(kwargs.get('server_name'), 'api.example.com')


@patch('apps.batch.shortcuts.execute_step')
class RefTokenResolution(TestCase):
    """Test that `@ref` tokens in paths and payloads are resolved from prior step results."""

    def test_resolves_path_reference_from_previous_step(self, mock_execute_step: Mock) -> None:
        """Verify `@ref` tokens in a later step's path are resolved from an earlier step's body."""

        mock_execute_step.side_effect = [
            (201, {'id': 42}),
            (200, {'detail': 'ok'}),
        ]
        steps = [
            {'ref': 'created', 'method': 'POST', 'path': '/items/', 'payload': {}},
            {'method': 'GET', 'path': '/items/@ref{created.id}/'},
        ]

        execute_job(steps)

        _method, path, *_ = mock_execute_step.call_args_list[1].args
        self.assertEqual(path, '/items/42/')

    def test_resolves_payload_reference_from_previous_step(self, mock_execute_step: Mock) -> None:
        """Verify `@ref` tokens in a later step's payload are resolved from an earlier step's body."""

        mock_execute_step.side_effect = [
            (201, {'id': 7}),
            (201, {}),
        ]
        steps = [
            {'ref': 'parent', 'method': 'POST', 'path': '/parents/', 'payload': {}},
            {'method': 'POST', 'path': '/children/', 'payload': {'parent_id': '@ref{parent.id}'}},
        ]

        execute_job(steps)

        _method, _path, payload, _query_params = mock_execute_step.call_args_list[1].args
        self.assertEqual(payload, {'parent_id': 7}, 'Whole-value @ref token should preserve int type')

    def test_propagates_reference_resolution_error(self, mock_execute_step: Mock) -> None:
        """Verify an unresolvable `@ref` token raises `ReferenceResolutionError` to the caller."""

        steps = [{'method': 'GET', 'path': '/items/@ref{ghost.id}/'}]

        with self.assertRaises(ReferenceResolutionError):
            execute_job(steps)

        mock_execute_step.assert_not_called()


@patch('apps.batch.shortcuts.execute_step')
class FileTokenResolution(TestCase):
    """Test that `@file` tokens in payloads are resolved against the supplied files dict."""

    def test_resolves_file_token_in_payload(self, mock_execute_step: Mock) -> None:
        """Verify `@file` tokens in payloads are resolved against the supplied files dict."""

        mock_execute_step.return_value = (201, {})
        upload = Mock()
        steps = [{'method': 'POST', 'path': '/uploads/', 'payload': {'file': '@file{doc}'}}]

        # Execute step with file payload matching referenced files
        execute_job(steps, files={'doc': upload})

        _method, _path, payload, _query_params = mock_execute_step.call_args_list[0].args
        self.assertIs(payload['file'], upload, 'File token should resolve to uploaded object')

    def test_propagates_reference_resolution_error(self, mock_execute_step: Mock) -> None:
        """Verify an unresolvable `@ref` token raises `ReferenceResolutionError` to the caller."""

        steps = [{'method': 'POST', 'path': '/uploads/', 'payload': {'file': '@file{doc}'}}]

        # Execute step without a file payload
        with self.assertRaises(ReferenceResolutionError):
            execute_job(steps)

        mock_execute_step.assert_not_called()


@patch('apps.batch.shortcuts.execute_step')
class ErrorHandling(TestCase):
    """Test the failure behaviour of `execute_job` when a step returns an error status."""

    def test_raises_job_execution_error_on_4xx(self, mock_execute_step: Mock) -> None:
        """Verify a step returning a 4xx status raises `JobExecutionError`."""

        mock_execute_step.return_value = (404, {'detail': 'not found'})
        steps = [{'method': 'GET', 'path': '/missing/'}]

        with self.assertRaises(JobExecutionError):
            execute_job(steps)

    def test_raises_job_execution_error_on_5xx(self, mock_execute_step: Mock) -> None:
        """Verify a step returning a 5xx status raises `JobExecutionError`."""

        mock_execute_step.return_value = (500, {'detail': 'error'})
        steps = [{'method': 'POST', 'path': '/items/'}]

        with self.assertRaises(JobExecutionError):
            execute_job(steps)

    def test_failure_stops_subsequent_steps(self, mock_execute_step: Mock) -> None:
        """Verify a failing step prevents later steps from executing."""

        # Setup — second step would succeed if reached
        mock_execute_step.side_effect = [(400, {'detail': 'bad'}), (200, {})]
        steps = [
            {'method': 'POST', 'path': '/a/'},
            {'method': 'GET', 'path': '/b/'},
        ]

        with self.assertRaises(JobExecutionError):
            execute_job(steps)

        self.assertEqual(mock_execute_step.call_count, 1, 'Steps after a failure must not execute')
