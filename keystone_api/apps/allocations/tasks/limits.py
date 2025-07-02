"""Background tasks for updating/enforcing Slurm usage limits."""

import logging

from celery import shared_task

from apps.allocations.models import *
from apps.users.models import *
from plugins import slurm

__all__ = ['update_limits', 'update_limit_for_account', 'update_limits_for_cluster']

log = logging.getLogger(__name__)


@shared_task()
def update_limits() -> None:
    """Adjust TRES billing limits for all Slurm accounts on all enabled clusters."""

    for cluster in Cluster.objects.filter(enabled=True).all():
        update_limits_for_cluster.delay(cluster.name)


@shared_task()
def update_limits_for_cluster(cluster_name: str) -> None:
    """Adjust TRES billing limits for all Slurm accounts on a given Slurm cluster.

    The Slurm accounts for `root` and any that are missing from Keystone are automatically ignored.

    Args:
        cluster_name: The name of the Slurm cluster to update.
    """

    cluster = Cluster.objects.get(name=cluster_name)
    for account_name in slurm.get_slurm_account_names(cluster.name):
        if account_name in ['root']:
            continue

        try:
            account = Team.objects.get(name=account_name)

        except Team.DoesNotExist:
            log.warning(f"No existing team for account '{account_name}' on cluster '{cluster.name}'.")
            continue

        update_limit_for_account(account, cluster)


def update_limit_for_account(account: Team, cluster: Cluster) -> None:
    """Update the allocation limits for an individual Slurm account and close out any expired allocations.

    Args:
        account: Team object for the account.
        cluster: Cluster object corresponding to the Slurm cluster.
    """

    # Calculate service units for expired and active allocations
    closing_sus = Allocation.objects.expiring_service_units(account, cluster)
    active_sus = Allocation.objects.active_service_units(account, cluster)

    # Determine the historical contribution to the current limit
    current_limit = slurm.get_cluster_limit(account.name, cluster.name)
    historical_usage = current_limit - active_sus - closing_sus

    if historical_usage < 0:
        historical_usage = 0
        log.warning(
            f"Negative historical usage calculated for account '{account.name}' on cluster '{cluster.name}':\n"
            f"  > current limit: {current_limit}\n"
            f"  > active sus: {active_sus}\n"
            f"  > expiring sus: {closing_sus}\n"
            f"  > historical usage: {historical_usage}\n"
            f"Assuming zero...")

    # Determine SUs used under the current allocations
    total_usage = slurm.get_cluster_usage(account.name, cluster.name)
    current_usage = total_usage - historical_usage
    if current_usage < 0:
        current_usage = historical_usage
        log.warning(
            f"Negative current usage calculated for account '{account.name}' on cluster '{cluster.name}':\n"
            f"  > total usage: {total_usage}\n"
            f"  > historical usage: {historical_usage}\n"
            f"  > current usage: {current_usage}\n"
            f"Defaulting to historical usage: {historical_usage}...")

    for allocation in Allocation.objects.expiring_allocations(account, cluster):
        allocation.final = min(current_usage, allocation.awarded)
        current_usage -= allocation.final
        allocation.save()

    # Users shouldn't be able to use more than their allocated service units.
    # If it does happen, create a warning so an admin can debug
    if current_usage > active_sus:
        log.warning(f"The system usage for account '{account.name}' exceeds its limit on cluster '{cluster.name}")

    # Set the new usage limit using the updated historical usage after closing any expired allocations
    updated_historical_usage = Allocation.objects.historical_usage(account, cluster)
    updated_limit = updated_historical_usage + active_sus
    slurm.set_cluster_limit(account.name, cluster.name, updated_limit)

    # Log summary of changes during limits update for this Slurm account on this cluster
    log.debug(
        f"Setting new TRES limit for account '{account.name}' on cluster '{cluster.name}':\n"
        f"  > limit change: {current_limit} -> {updated_limit}")
