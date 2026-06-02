"""Unit tests for the `update_limits_for_cluster` method."""

from unittest.mock import call, patch

from django.test import TestCase

from apps.allocations.factories import ClusterFactory
from apps.allocations.tasks.limits import update_limits_for_cluster
from apps.users.factories import TeamFactory


@patch("apps.allocations.tasks.limits.slurm")
@patch("apps.allocations.tasks.limits.update_limit_for_account")
class UpdateLimitsForClusterTask(TestCase):
    """Unit tests for the `update_limits_for_cluster` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.cluster = ClusterFactory(name="Cluster A")
        self.team_1 = TeamFactory(name="Team 1")
        self.team_2 = TeamFactory(name="Team 2")

    def test_updates_limit_for_each_matched_team(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify `update_limit_for_account` is called once per matched Slurm account."""

        mock_slurm.get_slurm_account_names.return_value = [self.team_1.slug, self.team_2.slug]

        update_limits_for_cluster(self.cluster.name)

        mock_update_limit_for_account.assert_has_calls(
            [call(self.team_1, self.cluster), call(self.team_2, self.cluster)],
            any_order=True,
        )
        self.assertEqual(mock_update_limit_for_account.call_count, 2)

    def test_skips_accounts_without_matching_team(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify Slurm accounts with no corresponding `Team` record produce no update call."""

        mock_slurm.get_slurm_account_names.return_value = [self.team_1.slug, "no-such-team"]

        update_limits_for_cluster(self.cluster.name)

        mock_update_limit_for_account.assert_called_once_with(self.team_1, self.cluster)

    def test_passes_correct_cluster_to_every_update_call(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify the resolved `Cluster` object is passed to every `update_limit_for_account` call."""

        mock_slurm.get_slurm_account_names.return_value = [self.team_1.slug, self.team_2.slug]

        update_limits_for_cluster(self.cluster.name)

        for dispatched_call in mock_update_limit_for_account.call_args_list:
            self.assertEqual(dispatched_call.args[1].pk, self.cluster.pk)

    def test_returns_early_when_cluster_does_not_exist(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify no Slurm calls are made when the cluster name is not found in the database."""

        update_limits_for_cluster("nonexistent-cluster")

        mock_slurm.get_slurm_account_names.assert_not_called()
        mock_update_limit_for_account.assert_not_called()

    def test_continues_after_exception_on_one_account(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify a failure updating one account does not prevent updates for subsequent accounts."""

        mock_slurm.get_slurm_account_names.return_value = [self.team_1.slug, self.team_2.slug]
        mock_update_limit_for_account.side_effect = [RuntimeError("Slurm failure"), None]

        update_limits_for_cluster(self.cluster.name)

        self.assertEqual(mock_update_limit_for_account.call_count, 2)
        mock_update_limit_for_account.assert_any_call(self.team_2, self.cluster)

    def test_does_not_update_teams_absent_from_cluster_account_list(self, mock_update_limit_for_account, mock_slurm) -> None:
        """Verify teams not present in the Slurm account list are not updated."""

        team_3 = TeamFactory(name="Team 3")
        mock_slurm.get_slurm_account_names.return_value = [self.team_1.slug]

        update_limits_for_cluster(self.cluster.name)

        updated_teams = [c.args[0] for c in mock_update_limit_for_account.call_args_list]
        self.assertNotIn(team_3, updated_teams)
