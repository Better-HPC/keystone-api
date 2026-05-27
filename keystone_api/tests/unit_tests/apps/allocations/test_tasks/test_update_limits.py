"""Unit tests for the `update_limits` task."""

from unittest.mock import call, patch

from django.test import TestCase

from apps.allocations.factories import ClusterFactory
from apps.allocations.models import Cluster
from apps.allocations.tasks.limits import update_limits


@patch("apps.allocations.tasks.limits.update_limits_for_cluster")
class UpdateLimitsMethod(TestCase):
    """Unit tests for the `update_limits` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.enabled_cluster_1 = ClusterFactory(name="Enabled Cluster 1")
        self.enabled_cluster_2 = ClusterFactory(name="Enabled Cluster 2")
        self.disabled_cluster = ClusterFactory(name="Disabled Cluster", enabled=False)

    def test_dispatches_enabled_clusters(self, mock_update_limits_for_cluster) -> None:
        """Verify a subtask is dispatched for every enabled cluster."""

        update_limits()
        mock_update_limits_for_cluster.delay.assert_has_calls(
            [call(self.enabled_cluster_1.name), call(self.enabled_cluster_2.name)],
            any_order=True,
        )

    def test_no_dispatches_for_disabled_clusters(self, mock_update_limits_for_cluster) -> None:
        """Verify disabled clusters produce no subtask dispatch."""

        update_limits()
        dispatched_names = [c.args[0] for c in mock_update_limits_for_cluster.delay.call_args_list]
        self.assertNotIn(self.disabled_cluster.name, dispatched_names)

    def test_no_enabled_clusters(self, mock_update_limits_for_cluster) -> None:
        """Verify no subtasks are dispatched when every cluster is disabled."""

        Cluster.objects.update(enabled=False)

        update_limits()
        mock_update_limits_for_cluster.delay.assert_not_called()

    def test_dispatches_cluster_name(self, mock_update_limits_for_cluster) -> None:
        """Verify each subtask receives the cluster name string, not the cluster object."""

        update_limits()
        for dispatched_call in mock_update_limits_for_cluster.delay.call_args_list:
            self.assertIsInstance(dispatched_call.args[0], str)
