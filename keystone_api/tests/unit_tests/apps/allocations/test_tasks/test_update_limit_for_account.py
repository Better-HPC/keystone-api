"""Unit tests for the `update_limit_for_account` function."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.allocations.factories import ClusterFactory, ResourceAllocationFactory
from apps.allocations.tasks.limits import update_limit_for_account
from apps.users.factories import TeamFactory

SLURM_MODULE = "apps.allocations.tasks.limits.slurm"


class UpdateLimitForAccountTests(TestCase):
    """Test the enforcement of slurm resource limits."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory(is_active=True)
        self.cluster = ClusterFactory()

    def _make_active_allocation(self, awarded: int) -> None:
        """Create an approved, currently active ResourceAllocation.

        Args:
            awarded: Number of service units to award the allocation.
        """

        today = date.today()
        ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=awarded,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=30),
            request__expire=today + timedelta(days=335),
        )

    def _make_expiring_allocation(self, awarded: int, final: int | None = None) -> None:
        """Create an approved, expired ResourceAllocation with no final usage set.

        Args:
            awarded: Number of service units originally awarded.
            final: Final usage value; defaults to None to simulate a pending expiring allocation.
        """

        today = date.today()
        ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=awarded,
            final=final,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=400),
            request__expire=today - timedelta(days=35),
        )

    def _make_historical_allocation(self, awarded: int, final: int) -> None:
        """Create a fully settled expired allocation with a final usage value.

        Args:
            awarded: Number of service units originally awarded.
            final: Final settled usage for the allocation.
        """

        self._make_expiring_allocation(awarded=awarded, final=final)

    # -------------------------------------------------------------------------
    # Happy path — active account, no expiring allocations
    # -------------------------------------------------------------------------

    @patch(SLURM_MODULE)
    def test_active_account_no_expiring_allocs(self, mock_slurm: MagicMock) -> None:
        """Verify the correct final limit is set for an active account with only settled historical allocations.

        active_sus=300, updated_historical=50; expected limit = 300 + 50 = 350.
        """

        self._make_active_allocation(awarded=300)
        self._make_historical_allocation(awarded=200, final=50)
        mock_slurm.get_cluster_limit.return_value = 350
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 350)

    @patch(SLURM_MODULE)
    def test_active_account_no_expiring_allocs_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once when there are no expiring allocations."""

        self._make_active_allocation(awarded=300)
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

        active_sus=300, expiring_sus=100; historical=500-300-100=100, current=350-100=250; min(250,100)=100.
        """

        self._make_active_allocation(awarded=300)
        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=100,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=date.today() - timedelta(days=400),
            request__expire=date.today() - timedelta(days=35),
        )
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 350

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertEqual(allocation.final, 100, "Allocation final should be capped at awarded value")

    @patch(SLURM_MODULE)
    def test_expiring_alloc_final_set_to_actual_usage(self, mock_slurm: MagicMock) -> None:
        """Verify a single expiring allocation final is set to actual usage when it is less than awarded.

        active_sus=300, expiring_sus=100 (awarded=200); historical=500-300-100=100,
        current=250-100=150; min(150,200)=150.
        """

        self._make_active_allocation(awarded=300)
        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=200,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=date.today() - timedelta(days=400),
            request__expire=date.today() - timedelta(days=35),
        )
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertEqual(allocation.final, 150, "Allocation final should equal actual usage when below awarded")

    @patch(SLURM_MODULE)
    def test_expiring_allocs_distributed_in_expiry_order(self, mock_slurm: MagicMock) -> None:
        """Verify current usage is distributed across expiring allocations ordered by expiration date.

        historical=500-300-200=0, current=400-0=400.
        alloc_a expires first (day -60): final=min(400,150)=150; remaining=250.
        alloc_b expires second (day -30): final=min(250,50)=50.
        """

        today = date.today()
        self._make_active_allocation(awarded=300)
        alloc_a = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=150,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=400),
            request__expire=today - timedelta(days=60),
        )
        alloc_b = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=50,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=400),
            request__expire=today - timedelta(days=30),
        )
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

        historical=400-300-0=100, current=200-100=100.
        alloc_x expires first (day -60): final=min(100,150)=100; remaining=0.
        alloc_y expires second (day -30): final=min(0,100)=0.
        """

        today = date.today()
        self._make_active_allocation(awarded=300)
        self._make_historical_allocation(awarded=200, final=100)
        alloc_x = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=150,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=400),
            request__expire=today - timedelta(days=60),
        )
        alloc_y = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=100,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=today - timedelta(days=400),
            request__expire=today - timedelta(days=30),
        )
        mock_slurm.get_cluster_limit.return_value = 400
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        alloc_x.refresh_from_db()
        alloc_y.refresh_from_db()
        self.assertEqual(alloc_x.final, 100, "First allocation should consume all available usage")
        self.assertEqual(alloc_y.final, 0, "Second allocation should receive zero when usage is exhausted")

    @patch(SLURM_MODULE)
    def test_expiring_alloc_finals_persisted_to_database(self, mock_slurm: MagicMock) -> None:
        """Verify computed final values are written to the database, not just set on in-memory objects."""

        self._make_active_allocation(awarded=300)
        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=100,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=date.today() - timedelta(days=400),
            request__expire=date.today() - timedelta(days=35),
        )
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

        historical=500-300-100=100, current=250-100=150; set_cluster_limit should receive 150.
        """

        self.team.is_active = False
        self.team.save()
        self._make_active_allocation(awarded=300)
        self._make_expiring_allocation(awarded=100)
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 150)

    @patch(SLURM_MODULE)
    def test_inactive_account_does_not_update_expiring_alloc_finals(self, mock_slurm: MagicMock) -> None:
        """Verify expiring allocation final values are not written when the account is inactive."""

        self.team.is_active = False
        self.team.save()
        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            awarded=100,
            final=None,
            request__team=self.team,
            request__status="AP",
            request__active=date.today() - timedelta(days=400),
            request__expire=date.today() - timedelta(days=35),
        )
        mock_slurm.get_cluster_limit.return_value = 500
        mock_slurm.get_cluster_usage.return_value = 250

        update_limit_for_account(self.team, self.cluster)

        allocation.refresh_from_db()
        self.assertIsNone(allocation.final, "Expiring allocation final should not be set for an inactive account")

    @patch(SLURM_MODULE)
    def test_inactive_account_zero_usage_locks_to_zero(self, mock_slurm: MagicMock) -> None:
        """Verify an inactive account with no recorded usage is locked to a limit of zero.

        historical=300-200-100=0, current=0-0=0; set_cluster_limit should receive 0.
        """

        self.team.is_active = False
        self.team.save()
        self._make_active_allocation(awarded=200)
        self._make_expiring_allocation(awarded=100)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 0

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 0)

    @patch(SLURM_MODULE)
    def test_inactive_account_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once for an inactive account due to early return."""

        self.team.is_active = False
        self.team.save()
        self._make_active_allocation(awarded=300)
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

        active_sus=200, expiring_sus=50; current_limit=100 → historical=100-200-50=-150 → clamped to 0.
        current=180-0=180.
        """

        self._make_active_allocation(awarded=200)
        self._make_expiring_allocation(awarded=50)
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

        active_sus=300; current_limit=500 → historical=500-300-0=200.
        total_usage=50 → current=50-200=-150 → clamped to historical=200.
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

        historical=500-300-0=200, current=650-200=450 > active_sus=300.
        Expected limit = updated_historical(200) + active_sus(300) = 500.
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
        """Verify a brand-new account with no allocations results in a Slurm limit of zero."""

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

        active_sus=400, updated_historical=75; expected limit = 400 + 75 = 475.
        """

        self._make_active_allocation(awarded=400)
        self._make_historical_allocation(awarded=200, final=75)
        mock_slurm.get_cluster_limit.return_value = 475
        mock_slurm.get_cluster_usage.return_value = 300

        update_limit_for_account(self.team, self.cluster)

        mock_slurm.set_cluster_limit.assert_called_once_with(self.team.name, self.cluster.name, 475)

    @patch(SLURM_MODULE)
    def test_active_account_calls_set_limit_once(self, mock_slurm: MagicMock) -> None:
        """Verify set_cluster_limit is called exactly once for a normal active account."""

        self._make_active_allocation(awarded=300)
        mock_slurm.get_cluster_limit.return_value = 300
        mock_slurm.get_cluster_usage.return_value = 200

        update_limit_for_account(self.team, self.cluster)

        self.assertEqual(
            mock_slurm.set_cluster_limit.call_count, 1,
            "set_cluster_limit should be called exactly once for an active account",
        )
