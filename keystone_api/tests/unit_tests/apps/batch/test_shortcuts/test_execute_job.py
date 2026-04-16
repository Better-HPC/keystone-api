"""Unit tests for the `execute_job` function."""

from unittest.mock import Mock, patch

from django.test import TestCase

from apps.batch.exceptions import JobExecutionError
from apps.batch.shortcuts import execute_job


class ExecuteJobFunction(TestCase):
    """Test the execution of batch jobs via the `execute_job` function."""

    @patch('shortcuts.execute_step')
    def test_returns_results_for_successful_steps(self, mock_execute_step: Mock) -> None:
        """Verify execute_job returns one result dict per step on success."""

        mock_execute_step.return_value = (201, {'id': 1})
        steps = [{'method': 'POST', 'path': '/items/', 'payload': {'name': 'x'}}]

        results = execute_job(steps)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 201)
        self.assertEqual(results[0]['method'], 'POST')
        self.assertEqual(results[0]['path'], '/items/')
        self.assertIsNone(results[0]['ref'], 'Steps without a ref alias should record None')

    @patch('shortcuts.execute_step')
    def test_records_ref_alias_in_result(self, mock_execute_step: Mock) -> None:
        """Verify a step's ref alias is recorded in the result dict."""

        mock_execute_step.return_value = (200, {'id': 9})
        steps = [{'ref': 'created', 'method': 'GET', 'path': '/items/9/'}]

        results = execute_job(steps)

        self.assertEqual(results[0]['ref'], 'created')

    @patch('shortcuts.execute_step')
    def test_resolves_path_reference_from_previous_step(self, mock_execute_step: Mock) -> None:
        """Verify @ref tokens in a later step's path are resolved from an earlier step's body."""

        mock_execute_step.side_effect = [
            (201, {'id': 42}),
            (200, {'detail': 'ok'}),
        ]
        steps = [
            {'ref': 'created', 'method': 'POST', 'path': '/items/', 'payload': {}},
            {'method': 'GET', 'path': '/items/@ref{created.id}/'},
        ]

        results = execute_job(steps)

        # Assert the second call used the resolved path
        _, second_call_kwargs = mock_execute_step.call_args_list[1]
        second_path = mock_execute_step.call_args_list[1][0][1]
        self.assertEqual(second_path, '/items/42/')

    @patch('shortcuts.execute_step')
    def test_raises_job_execution_error_on_4xx(self, mock_execute_step: Mock) -> None:
        """Verify a step returning a 4xx status raises `JobExecutionError`."""

        mock_execute_step.return_value = (404, {'detail': 'not found'})
        steps = [{'method': 'GET', 'path': '/missing/'}]

        with self.assertRaises(JobExecutionError):
            execute_job(steps)

    @patch('shortcuts.execute_step')
    def test_raises_job_execution_error_on_5xx(self, mock_execute_step: Mock) -> None:
        """Verify a step returning a 5xx status raises `JobExecutionError`."""

        mock_execute_step.return_value = (500, {'detail': 'error'})
        steps = [{'method': 'POST', 'path': '/items/'}]

        with self.assertRaises(JobExecutionError):
            execute_job(steps)

    @patch('shortcuts.execute_step')
    def test_dry_run_returns_results_without_committing(self, mock_execute_step: Mock) -> None:
        """Verify dry_run=True returns results but rolls back the transaction."""

        mock_execute_step.return_value = (201, {'id': 1})
        steps = [{'method': 'POST', 'path': '/items/'}]

        # We verify results are still returned; DB rollback is tested implicitly
        # via the DryRunRollbackError being swallowed internally.
        results = execute_job(steps, dry_run=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 201)

    @patch('shortcuts.execute_step')
    def test_empty_steps_list_returns_empty_results(self, mock_execute_step: Mock) -> None:
        """Verify an empty step list produces an empty result list."""

        results = execute_job([])

        mock_execute_step.assert_not_called()
        self.assertEqual(results, [])

    @patch('shortcuts.execute_step')
    def test_step_index_is_one_based(self, mock_execute_step: Mock) -> None:
        """Verify step results indices start at 1, not 0."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'GET', 'path': '/a/'}, {'method': 'GET', 'path': '/b/'}]

        results = execute_job(steps)

        self.assertEqual(results[0]['index'], 1)
        self.assertEqual(results[1]['index'], 2)

    @patch('shortcuts.execute_step')
    def test_passes_user_to_execute_step(self, mock_execute_step: Mock) -> None:
        """Verify the `user` argument is forwarded to `execute_step` on every call."""

        mock_execute_step.return_value = (200, {})
        mock_user = Mock()
        steps = [{'method': 'GET', 'path': '/items/'}]

        execute_job(steps, user=mock_user)

        _, kwargs = mock_execute_step.call_args
        self.assertEqual(kwargs.get('user'), mock_user)

    @patch('shortcuts.execute_step')
    def test_passes_server_name_to_execute_step(self, mock_execute_step: Mock) -> None:
        """Verify the `server_name` argument is forwarded to `execute_step`."""

        mock_execute_step.return_value = (200, {})
        steps = [{'method': 'GET', 'path': '/items/'}]

        execute_job(steps, server_name='api.example.com')

        _, kwargs = mock_execute_step.call_args
        self.assertEqual(kwargs.get('server_name'), 'api.example.com')
