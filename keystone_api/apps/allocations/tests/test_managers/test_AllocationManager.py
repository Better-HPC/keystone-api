"""Unit tests for the `AllocationManager` class."""

from django.test import TestCase
from django.utils import timezone

from apps.allocations.models import *
from apps.users.models import *


class GetAllocationData(TestCase):
    """Test getter methods used to retrieve allocation metadata/status."""

    def setUp(self) -> None:
        """Create test data."""

        self.user = User.objects.create(username="user", password='foobar123!')
        self.team = Team.objects.create(name="Research Team 1")
        self.cluster = Cluster.objects.create(name="Test Cluster")

        # An allocation request pending review
        self.request1 = AllocationRequest.objects.create(
            team=self.team,
            status='PD',
            active=timezone.now().date(),
            expire=timezone.now().date() + timezone.timedelta(days=30)
        )
        self.allocation1 = Allocation.objects.create(
            requested=100,
            awarded=80,
            final=None,
            cluster=self.cluster,
            request=self.request1
        )

        # An approved allocation request that is active
        self.request2 = AllocationRequest.objects.create(
            team=self.team,
            status='AP',
            active=timezone.now().date(),
            expire=timezone.now().date() + timezone.timedelta(days=30)
        )
        self.allocation2 = Allocation.objects.create(
            requested=100,
            awarded=80,
            final=None,
            cluster=self.cluster,
            request=self.request2
        )

        # An approved allocation request that is expired without final usage
        self.request3 = AllocationRequest.objects.create(
            team=self.team,
            status='AP',
            active=timezone.now().date() - timezone.timedelta(days=60),
            expire=timezone.now().date() - timezone.timedelta(days=30)
        )
        self.allocation3 = Allocation.objects.create(
            requested=100,
            awarded=70,
            final=None,
            cluster=self.cluster,
            request=self.request3
        )

        # An approved allocation request that is expired with final usage
        self.request4 = AllocationRequest.objects.create(
            team=self.team,
            status='AP',
            active=timezone.now().date() - timezone.timedelta(days=30),
            expire=timezone.now().date()
        )
        self.allocation4 = Allocation.objects.create(
            requested=100,
            awarded=60,
            final=60,
            cluster=self.cluster,
            request=self.request4
        )

    def test_approved_allocations(self) -> None:
        """Verify the `approved_allocations` method returns only approved allocations."""

        approved_allocations = Allocation.objects.approved_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation2, self.allocation3, self.allocation4]
        self.assertQuerySetEqual(expected_allocations, approved_allocations, ordered=False)

    def test_active_allocations(self) -> None:
        """Verify the `active_allocations` method returns only active allocations."""

        active_allocations = Allocation.objects.active_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation2]
        self.assertQuerySetEqual(expected_allocations, active_allocations, ordered=False)

    def test_expired_allocations(self) -> None:
        """Verify the `expired_allocations` method returns only expired allocations."""

        expiring_allocations = Allocation.objects.expiring_allocations(self.team, self.cluster)
        expected_allocations = [self.allocation3]
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
