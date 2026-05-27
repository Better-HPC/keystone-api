"""Unit tests for the `update_limit_for_account` function."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.allocations.factories import ClusterFactory, ResourceAllocationFactory
from apps.allocations.models import ResourceAllocation
from apps.allocations.tasks.limits import update_limit_for_account
from apps.users.factories import TeamFactory

SLURM_MODULE = "apps.allocations.tasks.limits.slurm"


# noinspection PyTypeChecker
@patch(SLURM_MODULE)
class UpdateLimitForAccountTests(TestCase):
    """Test the enforcement of slurm resource limits."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory(is_active=True)
        self.cluster = ClusterFactory()

    def _make_allocation(self, awarded: int, final: int | None, active: int, expires: int) -> ResourceAllocation:
        """Create an approved `ResourceAllocation` with fully specified date and usage values.

        Args:
            awarded: Number of service units originally awarded.
            final: Final recorded usage or `None` for allocations pending final settlement.
            active: Allocation start date as a day offset from today.
            expires: Allocation expiry date as a day offset from today.

        Returns:
            The created `ResourceAllocation` instance.
        """

        today = date.today()
        return ResourceAllocationFactory(
            cluster=self.cluster,
            requested=awarded,
            awarded=awarded,
            final=final,
            request__team=self.team,
            request__status="AP",
            request__active=today + timedelta(days=active),
            request__expire=today + timedelta(days=expires),
        )

    def test_account_with_no_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the cluster limit is set to zero when the account has no allocations.

        cluster: limit=0, usage=0
        result:  limit=0
        """

        mock_slurm.get_cluster_limit.return_value = 0
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)

    def test_account_with_new_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the cluster limit is increased when the account has new allocations.

        alloc_1: awarded=200, final=50,   active=now-400, expires=now-35
        alloc_2: awarded=300, final=None, active=now-30,  expires=now+335
        cluster: limit=350, usage=200
        result:  limit=350
        """

        alloc_1 = self._make_allocation(awarded=200, final=50, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 50
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 350)
        self.assertEqual(50, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_single_expiring_allocation_below_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify a single expiring allocation absorbs all current usage when below its awarded value.

        alloc_1: awarded=500,  final=None, active=now-400, expires=now-10
        alloc_2: awarded=1000, final=None, active=now-30,  expires=now+335
        cluster: limit=1500, usage=350
        result:  limit=1350, alloc_1.final=350
        """

        alloc_1 = self._make_allocation(awarded=500, final=None, active=-400, expires=-10)
        alloc_2 = self._make_allocation(awarded=1000, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 1500
        mock_slurm.get_cluster_usage.return_value = 350

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 1350)
        self.assertEqual(350, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_single_expiring_allocation_at_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify a single expiring allocation is finalized at its awarded value when fully consumed.

        alloc_1: awarded=500,  final=None, active=now-400, expires=now-10
        alloc_2: awarded=1000, final=None, active=now-30,  expires=now+335
        cluster: limit=1500, usage=500
        result:  limit=1500, alloc_1.final=500
        """

        alloc_1 = self._make_allocation(awarded=500, final=None, active=-400, expires=-10)
        alloc_2 = self._make_allocation(awarded=1000, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 1500
        mock_slurm.get_cluster_usage.return_value = 500

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 1500)
        self.assertEqual(500, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_account_with_usage_above_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify the expiring allocation's final usage is capped at the
        awarded SUs when usage exceeds it.

        alloc_1: awarded=100, final=None, active=now-400, expires=now-35
        alloc_2: awarded=300, final=None, active=now-30,  expires=now+335
        cluster: limit=500, usage=500
        result:  limit=400, alloc_1.final=100
        """

        alloc_1 = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 500

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 400)
        self.assertEqual(100, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_account_with_usage_below_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify the final resource usage is assigned to expiring allocations
        in order of their expiration date.

        alloc_1: awarded=200, final=100, active=now-400, expires=now-40
        alloc_2: awarded=100, final=None, active=now-400, expires=now-30
        alloc_3: awarded=100, final=None, active=now-400, expires=now-20
        alloc_4: awarded=100, final=None, active=now-400, expires=now-10
        alloc_5: awarded=100, final=None, active=now-30,  expires=now+335
        cluster: limit=500, usage=250
        result:  limit=350, alloc_2.final=100, alloc_3.final=50, alloc_4.final=0
        """

        alloc_1 = self._make_allocation(awarded=200, final=100, active=-400, expires=-40)
        alloc_2 = self._make_allocation(awarded=100, final=None, active=-400, expires=-30)
        alloc_3 = self._make_allocation(awarded=100, final=None, active=-400, expires=-20)
        alloc_4 = self._make_allocation(awarded=100, final=None, active=-400, expires=-10)
        alloc_5 = self._make_allocation(awarded=100, final=None, active=-30, expires=400)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2, alloc_3, alloc_4, alloc_5):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 350)
        self.assertEqual(100, alloc_1.final)
        self.assertEqual(100, alloc_2.final)
        self.assertEqual(50, alloc_3.final)
        self.assertEqual(0, alloc_4.final)
        self.assertIsNone(alloc_5.final)

    def test_multiple_expiring_allocations_at_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify all expiring allocations are finalized at their awarded values
        when usage fully consumes each one.

        alloc_1: awarded=200,  final=None, active=now-400, expires=now-30
        alloc_2: awarded=300,  final=None, active=now-400, expires=now-20
        alloc_3: awarded=1000, final=None, active=now-30,  expires=now+335
        cluster: limit=1500, usage=800
        result:  limit=1500, alloc_1.final=200, alloc_2.final=300
        """

        alloc_1 = self._make_allocation(awarded=200, final=None, active=-400, expires=-30)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-400, expires=-20)
        alloc_3 = self._make_allocation(awarded=1000, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 1500
        mock_slurm.get_cluster_usage.return_value = 800

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2, alloc_3):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 1500)
        self.assertEqual(200, alloc_1.final)
        self.assertEqual(300, alloc_2.final)
        self.assertIsNone(alloc_3.final)

    def test_active_account_with_zero_usage(self, mock_slurm: MagicMock) -> None:
        """Verify expiring allocations are finalized at zero when no current usage is recorded.

        alloc_1: awarded=500,  final=None, active=now-400, expires=now-30
        alloc_2: awarded=1000, final=None, active=now-30,  expires=now+335
        cluster: limit=1500, usage=0
        result:  limit=1000, alloc_1.final=0
        """

        alloc_1 = self._make_allocation(awarded=500, final=None, active=-400, expires=-30)
        alloc_2 = self._make_allocation(awarded=1000, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 1500
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 1000)
        self.assertEqual(0, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_account_with_only_expiring_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the limit collapses to historical usage when the account has no active allocations.

        alloc_1: awarded=500, final=None, active=now-400, expires=now-30
        cluster: limit=500, usage=300
        result:  limit=300, alloc_1.final=300
        """

        alloc_1 = self._make_allocation(awarded=500, final=None, active=-400, expires=-30)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 300

        update_limit_for_account(self.team, self.cluster)
        alloc_1.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 300)
        self.assertEqual(300, alloc_1.final)

    def test_active_account_with_negative_historical_usage(self, mock_slurm: MagicMock) -> None:
        """Verify historical usage is clamped to zero when it would otherwise be negative.

        alloc_1: awarded=50,  final=None, active=now-400, expires=now-35
        alloc_2: awarded=200, final=None, active=now-30,  expires=now+335
        cluster: limit=100, usage=180
        result:  limit=250, alloc_1.final=50
        """

        alloc_1 = self._make_allocation(awarded=50, final=None, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=200, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 100
        mock_slurm.get_cluster_usage.return_value = 180

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 250)
        self.assertEqual(50, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_active_account_with_negative_current_usage(self, mock_slurm: MagicMock) -> None:
        """Verify current usage falls back to historical usage when it would otherwise be negative.

        alloc_1: awarded=300, final=200,  active=now-400, expires=now-35
        alloc_2: awarded=300, final=None, active=now-30,  expires=now+335
        cluster: limit=500, usage=50
        result:  limit=500, alloc_1.final=200
        """

        alloc_1 = self._make_allocation(awarded=300, final=200, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 50

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 500)
        self.assertEqual(200, alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_inactive_account_with_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the cluster limit is locked to current usage without processing expiring allocations.

        alloc_1: awarded=100, final=None, active=now-400, expires=now-35
        alloc_2: awarded=300, final=None, active=now-30,  expires=now+335
        cluster: limit=500, usage=250
        result:  limit=150, alloc_1.final=None, alloc_2.final=None
        """

        self.team.is_active = False
        self.team.save()
        alloc_1 = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 150)
        self.assertIsNone(alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_inactive_account_with_zero_usage(self, mock_slurm: MagicMock) -> None:
        """Verify the cluster limit is locked to zero when the account has no recorded usage.

        alloc_1: awarded=100, final=None, active=now-400, expires=now-35
        alloc_2: awarded=200, final=None, active=now-30,  expires=now+335
        cluster: limit=300, usage=0
        result:  limit=0, alloc_1.final=None, alloc_2.final=None
        """

        self.team.is_active = False
        self.team.save()
        alloc_1 = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=200, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)
        self.assertIsNone(alloc_1.final)
        self.assertIsNone(alloc_2.final)

    def test_inactive_account_with_negative_current_usage(self, mock_slurm: MagicMock) -> None:
        """Verify current usage falls back to historical usage before locking the limit when the account is inactive.

        alloc_1: awarded=300, final=200,  active=now-400, expires=now-35
        alloc_2: awarded=300, final=None, active=now-30,  expires=now+335
        cluster: limit=500, usage=50
        result:  limit=200, alloc_1.final=200, alloc_2.final=None
        """

        self.team.is_active = False
        self.team.save()
        alloc_1 = self._make_allocation(awarded=300, final=200, active=-400, expires=-35)
        alloc_2 = self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 50

        update_limit_for_account(self.team, self.cluster)
        for alloc in (alloc_1, alloc_2):
            alloc.refresh_from_db()

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 200)
        self.assertEqual(200, alloc_1.final)
        self.assertIsNone(alloc_2.final)
