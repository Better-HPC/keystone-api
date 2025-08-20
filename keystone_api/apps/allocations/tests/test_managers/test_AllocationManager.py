"""Unit tests for the `AllocationManager` class."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.allocations.factories import AllocationFactory, AllocationRequestFactory, ClusterFactory
from apps.allocations.models import *
from apps.users.factories import TeamFactory, UserFactory


class GetAllocationData(TestCase):
    """Test getter methods used to retrieve allocation metadata/status."""

    def setUp(self) -> None:
        """Create test data."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

        # An allocation request pending review
        self.request_pending = AllocationRequestFactory(
            team=self.team,
            status='PD',
            active=timezone.now().date(),
            expire=timezone.now().date() + timedelta(days=30)
        )
        self.allocation_pending = AllocationFactory(
            requested=100,
            awarded=80,
            final=None,
            cluster=self.cluster,
            request=self.request_pending
        )

        # An approved allocation request that is active
        self.request_active = AllocationRequestFactory(
            team=self.team,
            status='AP',
            active=timezone.now().date(),
            expire=timezone.now().date() + timedelta(days=30)
        )
        self.allocation_active = AllocationFactory(
            requested=100,
            awarded=80,
            final=None,
            cluster=self.cluster,
            request=self.request_active
        )

        # An approved allocation request that is expired without final usage
        self.request_expired = AllocationRequestFactory(
            team=self.team,
            status='AP',
            active=timezone.now().date() - timedelta(days=60),
            expire=timezone.now().date() - timedelta(days=30)
        )
        self.allocation_expired = AllocationFactory(
            requested=100,
            awarded=70,
            final=None,
            cluster=self.cluster,
            request=self.request_expired
        )

        # An approved allocation request that is expired with final usage
        self.request4 = AllocationRequestFactory(
            team=self.team,
            status='AP',
            active=timezone.now().date() - timedelta(days=30),
            expire=timezone.now().date()
        )
        self.allocation4 = AllocationFactory(
            requested=100,
            awarded=60,
            final=60,
            cluster=self.cluster,
            request=self.request4
        )

    def test_approved_allocations(self) -> None:
        """Verify the `approved_allocations` method returns only approved allocations."""

        approved_allocations = Allocation.objects.approved_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation_active, self.allocation_expired, self.allocation4]
        self.assertQuerySetEqual(expected_allocations, approved_allocations, ordered=False)

    def test_active_allocations(self) -> None:
        """Verify the `active_allocations` method returns only active allocations."""

        active_allocations = Allocation.objects.active_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation_active]
        self.assertQuerySetEqual(expected_allocations, active_allocations, ordered=False)

    def test_expired_allocations(self) -> None:
        """Verify the `expired_allocations` method returns only expired allocations."""

        expiring_allocations = Allocation.objects.expiring_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation_expired]
        self.assertQuerySetEqual(expected_allocations, expiring_allocations, ordered=False)

    def test_active_service_units(self) -> None:
        """Verify the `active_service_units` method returns the total awarded service units for active allocations."""

        active_su = Allocation.objects.active_service_units(self.team, self.cluster)
        self.assertEqual(80, active_su)

    def test_expired_service_units(self) -> None:
        """Verify the `expired_service_units` method returns the total awarded service units for expired allocations."""

        expiring_su = Allocation.objects.expiring_service_units(self.team, self.cluster)
        self.assertEqual(70, expiring_su)

    def test_historical_usage(self) -> None:
        """Verify the `historical_usage` method returns the total final usage for expired allocations."""

        historical_usage = Allocation.objects.historical_usage(self.team, self.cluster)
        self.assertEqual(60, historical_usage)
