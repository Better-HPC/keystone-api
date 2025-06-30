"""Custom database managers for encapsulating repeatable table queries.

Manager classes encapsulate common database operations at the table level (as
opposed to the level of individual records). At least one Manager exists for
every database model. Managers are commonly exposed as an attribute of the
associated model class called `objects`.
"""

from datetime import date
from typing import TYPE_CHECKING

from django.db.models import Manager, QuerySet, Sum

from apps.users.models import Team

if TYPE_CHECKING:  # pragma: nocover
    from apps.allocations.models import Cluster

__all__ = ['AllocationManager', 'AllocationRequestManager']


class AllocationManager(Manager):
    """Custom manager for the `Allocation` model.

    Provides query methods for fetching approved, active, and expired allocations,
    as well as calculating service units and historical usage.
    """

    def approved_allocations(self, team: Team, cluster: 'Cluster') -> QuerySet:
        """Retrieve all approved allocations for a specific account and cluster.

        Args:
            team: The team to retrieve allocations for.
            cluster: The cluster to retrieve allocations for.

        Returns:
            A queryset of approved `Allocation` objects.
        """

        return self.filter(request__team=team, cluster=cluster, request__status='AP')

    def active_allocations(self, team: Team, cluster: 'Cluster') -> QuerySet:
        """Retrieve all active allocations for a specific account and cluster.

        Active allocations have been approved and are currently within their start/end date.

        Args:
            team: The team to retrieve allocations for.
            cluster: The cluster to retrieve allocations for.

        Returns:
            A queryset of active `Allocation` objects.
        """

        return self.approved_allocations(team, cluster).filter(
            request__active__lte=date.today(), request__expire__gt=date.today()
        )

    def expiring_allocations(self, team: Team, cluster: 'Cluster') -> QuerySet:
        """Retrieve all expiring allocations for a specific account and cluster.

        Expiring allocations have been approved and have passed their expiration date
        but do not yet have a final usage value set.

        Args:
            team: The team to retrieve allocations for.
            cluster: The cluster to retrieve allocations for.

        Returns:
            A queryset of expired Allocation objects ordered by expiration date.
        """

        return self.approved_allocations(team, cluster).filter(
            final=None, request__expire__lte=date.today()
        ).order_by("request__expire")

    def active_service_units(self, team: Team, cluster: 'Cluster') -> int:
        """Calculate the total service units across all active allocations for an account and cluster.

        Active allocations have been approved and are currently within their start/end date.

        Args:
            team: The team to calculate service units for.
            cluster: The cluster to retrieve service units for.

        Returns:
            Total service units from active allocations.
        """

        return self.active_allocations(team, cluster).aggregate(
            Sum("awarded")
        )['awarded__sum'] or 0

    def expiring_service_units(self, team: Team, cluster: 'Cluster') -> int:
        """Calculate the total service units across all expiring allocations for an account and cluster.

        Expiring allocations have been approved and have passed their expiration date
        but do not yet have a final usage value set.

        Args:
            team: The team to calculate service units for.
            cluster: The cluster to calculate service units for.

        Returns:
            Total service units from expired allocations.
        """

        return self.expiring_allocations(team, cluster).aggregate(
            Sum("awarded")
        )['awarded__sum'] or 0

    def historical_usage(self, team: Team, cluster: 'Cluster') -> int:
        """Calculate the total final usage for expired allocations of a specific account and cluster.

        Args:
            team: The team to calculate usage totals for.
            cluster: The cluster to calculate usage totals for.

        Returns:
            Total historical usage calculated from expired allocations.
        """

        return self.approved_allocations(team, cluster).filter(
            request__expire__lte=date.today()
        ).aggregate(Sum("final"))['final__sum'] or 0


class AllocationRequestManager(Manager):
    """Custom manager for the `AllocationRequest` model.

    Provides query methods for fetching requests by team and status.
    """

    def active_requests(self, team: Team) -> QuerySet:
        """Return all active allocation requests for a specific team.

        Args:
            team: The team to return requests for.

        Returns:
            A queryset of active `AllocationRequest` objects.
        """

        return self.filter(
            team=team,
            status='AP',
            request__active__lte=date.today(),
            request__expire__gt=date.today()
        )

    def pending_requests(self, team: Team) -> QuerySet:
        """Return all pending allocation requests for a specific team.

        Args:
            team: The team to return requests for.

        Returns:
            A queryset of pending `AllocationRequest` objects.
        """

        return self.filter(team=team, status='PD')
