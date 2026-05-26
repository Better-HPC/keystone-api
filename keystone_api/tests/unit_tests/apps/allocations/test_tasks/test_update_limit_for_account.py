"""Unit tests for the `update_limit_for_account` function."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.allocations.factories import ClusterFactory, ResourceAllocationFactory
from apps.allocations.tasks.limits import update_limit_for_account
from apps.users.factories import TeamFactory

SLURM_MODULE = "apps.allocations.tasks.limits.slurm"


# noinspection PyTypeChecker
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

    @patch(SLURM_MODULE)
    def test_active_account_with_no_expiring_allocs(self, mock_slurm: MagicMock) -> None:
        """Verify the limit is set to active_sus plus historical_usage.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=200, final=50,   active=now-400, expires=now-35
        cluster:  limit=350, usage=200
        result:   historical=50, limit=350
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        self._make_allocation(awarded=200, final=50, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 350
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 350)

    @patch(SLURM_MODULE)
    def test_active_account_with_usage_below_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify the expiring allocation final is set to actual usage when it is less than awarded.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=200, final=None, active=now-400, expires=now-35
        cluster:  limit=500, usage=250
        result:   historical=0, current=250 → alloc_2.final=min(250, 200)=150
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        allocation = self._make_allocation(awarded=200, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertEqual(allocation.final, 150, "Expiring allocation final should equal actual usage when below awarded")

    @patch(SLURM_MODULE)
    def test_active_account_with_usage_exceeds_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify the expiring allocation final is capped at awarded when usage exceeds it.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=100, final=None, active=now-400, expires=now-35
        cluster:  limit=500, usage=350
        result:   historical=100, current=250 → alloc_2.final=min(250, 100)=100
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        allocation = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 350

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertEqual(allocation.final, 100, "Expiring allocation final should be capped at awarded value")

    @patch(SLURM_MODULE)
    def test_active_account_with_remaining_usage(self, mock_slurm: MagicMock) -> None:
        """Verify usage is distributed across expiring allocations in order of expiration date.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=150, final=None, active=now-400, expires=now-60
        alloc_3:  awarded=50,  final=None, active=now-400, expires=now-30
        cluster:  limit=500, usage=400
        result:   historical=0, current=400 → alloc_2.final=150, remaining=250 → alloc_3.final=50
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        alloc_a = self._make_allocation(awarded=150, final=None, active=-400, expires=-60)
        alloc_b = self._make_allocation(awarded=50, final=None, active=-400, expires=-30)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 400

        update_limit_for_account(self.team, self.cluster)

        alloc_a.refresh_from_db()
        alloc_b.refresh_from_db()
        self.assertEqual(alloc_a.final, 150, "Earlier expiring allocation should consume usage up to its awarded value")
        self.assertEqual(alloc_b.final, 50, "Later expiring allocation should receive the remaining usage")

    @patch(SLURM_MODULE)
    def test_active_account_with_exhausted_usage(self, mock_slurm: MagicMock) -> None:
        """Verify later expiring allocations receive a final of zero when usage is fully consumed by earlier ones.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=200, final=100,  active=now-400, expires=now-35
        alloc_3:  awarded=150, final=None, active=now-400, expires=now-60
        alloc_4:  awarded=100, final=None, active=now-400, expires=now-30
        cluster:  limit=400, usage=200
        result:   historical=100, current=100 → alloc_3.final=100, remaining=0 → alloc_4.final=0
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        self._make_allocation(awarded=200, final=100, active=-400, expires=-35)
        alloc_x = self._make_allocation(awarded=150, final=None, active=-400, expires=-60)
        alloc_y = self._make_allocation(awarded=100, final=None, active=-400, expires=-30)
        mock_slurm.get_cluster_limit.return_value = 400
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        alloc_x.refresh_from_db()
        alloc_y.refresh_from_db()
        self.assertEqual(alloc_x.final, 100, "Earlier expiring allocation should consume all available usage")
        self.assertEqual(alloc_y.final, 0, "Later expiring allocation should receive zero when usage is exhausted")

    @patch(SLURM_MODULE)
    def test_active_account_with_no_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the limit is set to zero when the account has no allocations.

        cluster:  limit=0, usage=0
        result:   historical=0, current=0, limit=0
        """

        mock_slurm.get_cluster_limit.return_value = 0
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)

    @patch(SLURM_MODULE)
    def test_active_account_with_usage_exceeds_active_sus(self, mock_slurm: MagicMock) -> None:
        """Verify the limit is set correctly when current usage exceeds active_sus.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=300, final=200,  active=now-400, expires=now-35
        cluster:  limit=500, usage=650
        result:   historical=200, current=450 > active_sus=300 → limit=200+300=500
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        self._make_allocation(awarded=300, final=200, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 650

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 500)

    @patch(SLURM_MODULE)
    def test_active_account_with_negative_historical_usage(self, mock_slurm: MagicMock) -> None:
        """Verify historical_usage is clamped to zero when it would otherwise be negative.

        alloc_1:  awarded=200, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=50,  final=None, active=now-400, expires=now-35
        cluster:  limit=100, usage=180
        result:   historical=100-200-50=-150 → clamped to 0, current=180, limit=0+200=200
        """

        self._make_allocation(awarded=200, final=None, active=-30, expires=335)
        self._make_allocation(awarded=50, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 100
        mock_slurm.get_cluster_usage.return_value = 180

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 200)

    @patch(SLURM_MODULE)
    def test_active_account_with_negative_current_usage(self, mock_slurm: MagicMock) -> None:
        """Verify current_usage falls back to historical_usage when it would otherwise be negative.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=300, final=200,  active=now-400, expires=now-35
        cluster:  limit=500, usage=50
        result:   historical=200, current=50-200=-150 → clamped to historical=200, limit=200+300=500
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        self._make_allocation(awarded=300, final=200, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 50

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 500)

    @patch(SLURM_MODULE)
    def test_inactive_account_with_allocations(self, mock_slurm: MagicMock) -> None:
        """Verify the limit is locked to current_usage without processing expiring allocations.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=100, final=None, active=now-400, expires=now-35
        cluster:  limit=500, usage=250
        result:   historical=100, current=150 → account inactive, limit=150
        """

        self.team.is_active = False
        self.team.save()
        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 150)

    @patch(SLURM_MODULE)
    def test_inactive_account_with_expiring_allocs(self, mock_slurm: MagicMock) -> None:
        """Verify expiring allocation finals are not written when the account is inactive.

        alloc_1:  awarded=100, final=None, active=now-400, expires=now-35
        cluster:  limit=500, usage=250
        result:   account inactive → early return, alloc_1.final remains None
        """

        self.team.is_active = False
        self.team.save()
        allocation = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertIsNone(allocation.final, "Expiring allocation final should not be set for an inactive account")

    @patch(SLURM_MODULE)
    def test_inactive_account_with_zero_usage(self, mock_slurm: MagicMock) -> None:
        """Verify the limit is locked to zero when the account has no recorded usage.

        alloc_1:  awarded=200, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=100, final=None, active=now-400, expires=now-35
        cluster:  limit=300, usage=0
        result:   historical=0, current=0 → account inactive, limit=0
        """

        self.team.is_active = False
        self.team.save()
        self._make_allocation(awarded=200, final=None, active=-30, expires=335)
        self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)
