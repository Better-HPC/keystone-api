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
class UpdateLimitForAccountTests(TestCase):
    """Test the enforcement of slurm resource limits."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory(is_active=True)
        self.cluster = ClusterFactory()

    def _make_allocation(self, awarded: int, final: int | None, active: int, expires: int) -> ResourceAllocation:
        """Create an approved ResourceAllocation with fully specified date and usage values.

        Args:
            awarded: Number of service units originally awarded.
            final: Final recorded usage; pass `None` for allocations pending final settlement.
            active: Allocation start date as a day offset from today (negative = past).
            expires: Allocation expiry date as a day offset from today (negative = past, positive = future).

        Returns:
            The created ResourceAllocation instance.
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
    def test_active_account_no_expiring_allocs(self, mock_slurm: MagicMock) -> None:
        """Verify the final limit equals active_sus plus historical_usage when no allocations are pending final settlement.

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
    def test_active_account_no_expiring_allocs_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once when there are no expiring allocations.

        alloc_1:  awarded=300, final=None, active=now-30, expires=now+335
        cluster:  limit=300, usage=100
        result:   historical=0, current=100, limit=300
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 100

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once()

    # -------------------------------------------------------------------------
    # Expiring allocations — distribution logic
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_expiring_alloc_final_capped_at_awarded(self, mock_slurm: MagicMock) -> None:
        """Verify a single expiring allocation has its final value capped at awarded when usage exceeds it.

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
        self.assertEqual(allocation.final, 100, "Allocation final should be capped at awarded value")

    @patch(SLURM_MODULE)
    def test_expiring_alloc_final_set_to_actual_usage(self, mock_slurm: MagicMock) -> None:
        """Verify a single expiring allocation final is set to actual usage when it is less than awarded.

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
        self.assertEqual(allocation.final, 150, "Allocation final should equal actual usage when below awarded")

    @patch(SLURM_MODULE)
    def test_expiring_allocs_distributed_in_expiry_order(self, mock_slurm: MagicMock) -> None:
        """Verify current usage is distributed across expiring allocations in order of expiration date.

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
        self.assertEqual(alloc_a.final, 150, "First allocation should consume up to its awarded value")
        self.assertEqual(alloc_b.final, 50, "Second allocation should receive the remaining usage")

    @patch(SLURM_MODULE)
    def test_expiring_allocs_receive_zero_when_usage_exhausted(self, mock_slurm: MagicMock) -> None:
        """Verify later expiring allocations receive final=0 once current usage is fully consumed by earlier ones.

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
        self.assertEqual(alloc_x.final, 100, "First allocation should consume all available usage")
        self.assertEqual(alloc_y.final, 0, "Second allocation should receive zero when usage is exhausted")

    @patch(SLURM_MODULE)
    def test_expiring_alloc_finals_persisted_to_database(self, mock_slurm: MagicMock) -> None:
        """Verify computed final values are written to the database, not just set on in-memory objects.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=100, final=None, active=now-400, expires=now-35
        cluster:  limit=500, usage=250
        result:   historical=100, current=150 → alloc_2.final=100, persisted to database
        """

        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        allocation = self._make_allocation(awarded=100, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertIsNotNone(allocation.final, "Expiring allocation final value should be persisted to the database")

    # -------------------------------------------------------------------------
    # Inactive account — early return
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_inactive_account_locks_to_current_usage(self, mock_slurm: MagicMock) -> None:
        """Verify an inactive account has its limit locked to current_usage without processing expiring allocations.

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
    def test_inactive_account_does_not_update_expiring_alloc_finals(self, mock_slurm: MagicMock) -> None:
        """Verify expiring allocation final values are not written when the account is inactive.

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
    def test_inactive_account_zero_usage_locks_to_zero(self, mock_slurm: MagicMock) -> None:
        """Verify an inactive account with no recorded usage is locked to a limit of zero.

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

    @patch(SLURM_MODULE)
    def test_inactive_account_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once for an inactive account due to early return.

        alloc_1:  awarded=300, final=None, active=now-30, expires=now+335
        cluster:  limit=500, usage=250
        result:   account inactive → early return after single set_cluster_limit call
        """

        self.team.is_active = False
        self.team.save()
        self._make_allocation(awarded=300, final=None, active=-30, expires=335)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        self.assertEqual(
            mock_slurm.set_cluster_limit.call_count, 1,
            "set_cluster_limit should be called exactly once for inactive accounts",
        )

    # -------------------------------------------------------------------------
    # Edge case: negative historical_usage (clamped to 0)
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_negative_historical_usage_clamped(self, mock_slurm: MagicMock) -> None:
        """Verify execution completes normally when historical_usage is negative and is clamped to zero.

        alloc_1:  awarded=200, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=50,  final=None, active=now-400, expires=now-35
        cluster:  limit=100, usage=180
        result:   historical=100-200-50=-150 → clamped to 0, current=180
        """

        self._make_allocation(awarded=200, final=None, active=-30, expires=335)
        self._make_allocation(awarded=50, final=None, active=-400, expires=-35)
        mock_slurm.get_cluster_limit.return_value = 100
        mock_slurm.get_cluster_usage.return_value = 180

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once()

    # -------------------------------------------------------------------------
    # Edge case: negative current_usage (fallback to historical_usage)
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_negative_current_usage_falls_back_to_historical(self, mock_slurm: MagicMock) -> None:
        """Verify execution completes normally when current_usage is negative and falls back to historical_usage.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=300, final=200,  active=now-400, expires=now-35
        cluster:  limit=500, usage=50
        result:   historical=200, current=50-200=-150 → clamped to historical=200
        """

        self._make_active_allocation(awarded=300)
        self._make_historical_allocation(awarded=300, final=200)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 50

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once()

    # -------------------------------------------------------------------------
    # Edge case: current_usage > active_sus (over-usage)
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_over_usage_produces_correct_limit(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is still called with the correct value when current_usage exceeds active_sus.

        alloc_1:  awarded=300, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=300, final=200,  active=now-400, expires=now-35
        cluster:  limit=500, usage=650
        result:   historical=200, current=450 > active_sus=300 → limit=200+300=500
        """

        self._make_active_allocation(awarded=300)
        self._make_historical_allocation(awarded=300, final=200)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 650

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 500)

    # -------------------------------------------------------------------------
    # Edge case: all zeroes (empty/new account)
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_zero_sus_produces_zero_limit(self, mock_slurm: MagicMock) -> None:
        """Verify a brand-new account with no allocations results in a Slurm limit of zero.

        cluster:  limit=0, usage=0
        result:   historical=0, current=0, limit=0
        """

        mock_slurm.get_cluster_limit.return_value = 0
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)

    # -------------------------------------------------------------------------
    # Final limit value correctness
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_final_limit_equals_updated_historical_plus_active_sus(self, mock_slurm: MagicMock) -> None:
        """Verify the value passed to set_cluster_limit is updated_historical_usage + active_sus.

        alloc_1:  awarded=400, final=None, active=now-30,  expires=now+335
        alloc_2:  awarded=200, final=75,   active=now-400, expires=now-35
        cluster:  limit=475, usage=300
        result:   historical=75, current=225, limit=75+400=475
        """

        self._make_active_allocation(awarded=400)
        self._make_historical_allocation(awarded=200, final=75)
        mock_slurm.get_cluster_limit.return_value = 475
        mock_slurm.get_cluster_usage.return_value = 300

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 475)

    @patch(SLURM_MODULE)
    def test_active_account_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once for a normal active account.

        alloc_1:  awarded=300, final=None, active=now-30, expires=now+335
        cluster:  limit=300, usage=200
        result:   historical=0, current=200, limit=300
        """

        self._make_active_allocation(awarded=300)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        self.assertEqual(
            mock_slurm.set_cluster_limit.call_count, 1,
            "set_cluster_limit should be called exactly once for an active account",
        )
