"""Unit tests for the `AllocationManager` class."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.allocations.factories import ResourceAllocationFactory, AllocationRequestFactory, ClusterFactory
from apps.allocations.models import ResourceAllocation
from apps.users.factories import TeamFactory


class ApprovedAllocationsMethod(TestCase):
    """Test the fetching of approved allocations."""

    def setUp(self) -> None:
        """Instantiate common test fixtures."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

    def test_includes_active_approved_allocations(self) -> None:
        """Verify active, approved allocations are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date(),
                expire=timezone.now().date() + timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.approved_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_includes_expired_approved_allocations(self) -> None:
        """Verify expired, approved allocations are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=60),
                expire=timezone.now().date() - timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.approved_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_includes_upcoming_approved_allocations(self) -> None:
        """Verify upcoming, approved allocations are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() + timedelta(days=30),
                expire=timezone.now().date() + timedelta(days=60),
            )
        )

        results = ResourceAllocation.objects.approved_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_includes_approved_allocations_with_no_dates(self) -> None:
        """Verify allocations with no start/end date are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            final=None,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=None, expire=None
            )
        )

        results = ResourceAllocation.objects.approved_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_excludes_pending_allocations(self) -> None:
        """Verify pending allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",
                active=timezone.now().date(),
                expire=timezone.now().date() + timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.approved_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)


class ActiveAllocationsMethod(TestCase):
    """Test the fetching of active allocations."""

    def setUp(self) -> None:
        """Instantiate common test fixtures."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

    def test_includes_active_approved_allocations(self) -> None:
        """Verify currently active allocations are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=30),
                expire=timezone.now().date() + timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.active_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_excludes_expired_approved_allocations(self) -> None:
        """Verify expired, approved allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=60),
                expire=timezone.now().date() - timedelta(days=30),  # expired
            )
        )

        results = ResourceAllocation.objects.active_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)

    def test_excludes_upcoming_approved_allocations(self) -> None:
        """Verify upcoming, approved allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() + timedelta(days=30),  # future start
                expire=timezone.now().date() + timedelta(days=60),
            )
        )

        results = ResourceAllocation.objects.active_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)

    def test_includes_approved_allocations_with_no_expiration(self) -> None:
        """Verify allocations with no end date are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            final=None,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=60),
                expire=None,
            )
        )

        results = ResourceAllocation.objects.active_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_excludes_pending_allocations(self) -> None:
        """Verify pending allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",
                active=timezone.now().date() - timedelta(days=30),
                expire=timezone.now().date() + timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.active_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)


class ExpiringAllocationsMethod(TestCase):
    """Test the fetching of expiring allocations."""

    def setUp(self) -> None:
        """Instantiate common test fixtures."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

    def test_includes_expiring_allocations(self) -> None:
        """Verify expiring allocations are included in the returned queryset."""

        allocation = ResourceAllocationFactory(
            cluster=self.cluster,
            final=None,  # None signifies the expiration has not been processed yet
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=60),
                expire=timezone.now().date() - timedelta(days=30),  # past expiration
            )
        )

        results = ResourceAllocation.objects.expiring_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([allocation], results, ordered=False)

    def test_excludes_allocations_with_final_usage(self) -> None:
        """Verify expired allocations with a known final usage are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            final=0,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=60),
                expire=timezone.now().date() - timedelta(days=30),  # past expiration
            )
        )

        results = ResourceAllocation.objects.expiring_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)

    def test_excludes_active_approved_allocations(self) -> None:
        """Verify active, approved allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() - timedelta(days=30),
                expire=timezone.now().date() + timedelta(days=30),  # still active
            )
        )

        results = ResourceAllocation.objects.expiring_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)

    def test_excludes_upcoming_approved_allocations(self) -> None:
        """Verify upcoming, approved allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=timezone.now().date() + timedelta(days=30),  # not started yet
                expire=timezone.now().date() + timedelta(days=60),
            )
        )

        results = ResourceAllocation.objects.expiring_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)

    def test_excludes_pending_request(self) -> None:
        """Verify pending allocations are not included in the returned queryset."""

        ResourceAllocationFactory(
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",  # not approved
                active=timezone.now().date() - timedelta(days=60),
                expire=timezone.now().date() - timedelta(days=30),
            )
        )

        results = ResourceAllocation.objects.expiring_allocations(self.team, self.cluster)
        self.assertQuerySetEqual([], results, ordered=False)


class ActiveServiceUnitsMethod(TestCase):
    """Test the calculation of active service units."""

    def setUp(self) -> None:
        """Instantiate test fixtures covering multiple edge cases."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

        today = timezone.now().date()

        # Active, approved allocation (included)
        self.active_allocation = ResourceAllocationFactory(
            awarded=60,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today,
                expire=today + timedelta(days=30),
            )
        )

        # Expired allocation (excluded)
        ResourceAllocationFactory(
            awarded=50,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

        # Upcoming allocation (excluded)
        ResourceAllocationFactory(
            awarded=40,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today + timedelta(days=5),
                expire=today + timedelta(days=40),
            )
        )

        # Active with no expiration (included)
        self.no_expire_allocation = ResourceAllocationFactory(
            awarded=30,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=10),
                expire=None,
            )
        )

        # Pending request (excluded)
        ResourceAllocationFactory(
            awarded=20,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",
                active=today,
                expire=today + timedelta(days=30),
            )
        )

    def test_service_unit_calculation(self) -> None:
        """Verify active service units only sum from currently active, approved allocations."""

        included_allocations = [self.active_allocation, self.no_expire_allocation]

        expected_su = sum(a.awarded for a in included_allocations)
        returned_su = ResourceAllocation.objects.active_service_units(self.team, self.cluster)
        self.assertEqual(expected_su, returned_su)


class ExpiringServiceUnitsMethod(TestCase):
    """Test the calculation of expiring service units."""

    def setUp(self) -> None:
        """Instantiate test fixtures covering multiple edge cases."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

        today = timezone.now().date()

        # Expiring allocation - not yet processed (included)
        self.expiring_allocation = ResourceAllocationFactory(
            awarded=60,
            final=None,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

        # Expired allocation - already processed (excluded)
        self.expired_allocation = ResourceAllocationFactory(
            awarded=50,
            final=10,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

        # Active allocation (excluded)
        ResourceAllocationFactory(
            awarded=40,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=10),
                expire=today + timedelta(days=20),
            )
        )

        # Upcoming allocation (excluded)
        ResourceAllocationFactory(
            awarded=30,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today + timedelta(days=5),
                expire=today + timedelta(days=40),
            )
        )

        # Pending request (excluded)
        ResourceAllocationFactory(
            awarded=20,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

    def test_service_unit_calculation(self) -> None:
        """Verify expiring service units only sum from expiring, approved allocations."""

        included_allocations = [self.expiring_allocation, ]

        expected_su = sum(a.awarded for a in included_allocations)
        returned_su = ResourceAllocation.objects.expiring_service_units(self.team, self.cluster)
        self.assertEqual(expected_su, returned_su)


class HistoricalUsageMethod(TestCase):
    """Test the calculation of historical service units."""

    def setUp(self) -> None:
        """Instantiate test fixtures covering multiple edge cases."""

        self.team = TeamFactory()
        self.cluster = ClusterFactory()

        today = timezone.now().date()

        # Expired allocation with final usage (included)
        self.expired_with_final = ResourceAllocationFactory(
            final=60,
            awarded=70,  # awarded doesn't matter here
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

        # Expired allocation without final usage (excluded)
        ResourceAllocationFactory(
            final=None,
            awarded=50,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=90),
                expire=today - timedelta(days=60),
            )
        )

        # Active allocation (excluded)
        ResourceAllocationFactory(
            final=None,
            awarded=80,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=10),
                expire=today + timedelta(days=20),
            )
        )

        # Upcoming allocation (excluded)
        ResourceAllocationFactory(
            final=None,
            awarded=40,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today + timedelta(days=5),
                expire=today + timedelta(days=40),
            )
        )

        # Pending allocation (excluded)
        ResourceAllocationFactory(
            final=None,
            awarded=30,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="PD",
                active=today - timedelta(days=60),
                expire=today - timedelta(days=30),
            )
        )

        # Active allocation with no expiration (excluded)
        ResourceAllocationFactory(
            final=None,
            awarded=20,
            cluster=self.cluster,
            request=AllocationRequestFactory(
                team=self.team, status="AP",
                active=today - timedelta(days=10),
                expire=None,
            )
        )

    def test_service_unit_calculation(self) -> None:
        """Verify historical usage only sums the final values of expired allocations."""

        included_allocations = [self.expired_with_final, ]

        expected_usage = sum(a.final for a in included_allocations)
        returned_usage = ResourceAllocation.objects.historical_usage(self.team, self.cluster)
        self.assertEqual(expected_usage, returned_usage)
