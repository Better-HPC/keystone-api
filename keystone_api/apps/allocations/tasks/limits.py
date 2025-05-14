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
        update_limits_for_cluster(cluster)


@shared_task()
def update_limits_for_cluster(cluster: Cluster) -> None:
    """Adjust TRES billing limits for all Slurm accounts on a given Slurm cluster.

    The Slurm accounts for `root` and any that are missing from Keystone are automatically ignored.

    Args:
        cluster: The name of the Slurm cluster.
    """

    for account_name in slurm.get_slurm_account_names(cluster.name):
        if account_name in ['root']:
            continue

        try:
            account = Team.objects.get(name=account_name)

        except Team.DoesNotExist:
            log.warning(f"No existing team for account {account_name} on {cluster.name}, skipping for now")
            continue

        update_limit_for_account(account, cluster)


@shared_task()
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
        log.warning(f"Negative Historical usage found for {account.name} on {cluster.name}:\n"
                    f"historical: {historical_usage}, current: {current_limit}, active: {active_sus}, closing: {closing_sus}\n"
                    f"Assuming zero...")
        historical_usage = 0

    # Close expired allocations and determine the current usage
    total_usage = slurm.get_cluster_usage(account.name, cluster.name)
    current_usage = total_usage - historical_usage
    if current_usage < 0:
        log.warning(f"Negative Current usage found for {account.name} on {cluster.name}:\n"
                    f"current: {current_usage} = total: {total_usage} - historical: {historical_usage}\n"
                    f"Setting to historical usage: {historical_usage}...")
        current_usage = historical_usage

    closing_summary = (f"Summary of closing allocations:\n"
                       f"> Current Usage before closing: {current_usage}\n")
    for allocation in Allocation.objects.expiring_allocations(account, cluster):
        allocation.final = min(current_usage, allocation.awarded)
        closing_summary += f"> Allocation {allocation.id}: {current_usage} - {allocation.final} -> {current_usage - allocation.final}\n"
        current_usage -= allocation.final
        allocation.save()
    closing_summary += f"> Current Usage after closing: {current_usage}"

    # This shouldn't happen but if it does somehow, create a warning so an admin will notice
    if current_usage > active_sus:
        log.warning(f"The current usage is somehow higher than the limit for {account.name}!")

    # Set the new account usage limit using the updated historical usage after closing any expired allocations
    updated_historical_usage = Allocation.objects.historical_usage(account, cluster)
    updated_limit = updated_historical_usage + active_sus
    slurm.set_cluster_limit(account.name, cluster.name, updated_limit)

    # Log summary of changes during limits update for this Slurm account on this cluster
    log.debug(f"Summary of limits update for {account.name} on {cluster.name}:\n"
              f"> Service units from active allocations: {active_sus}\n"
              f"> Service units from closing allocations: {closing_sus}\n"
              f"> {closing_summary}\n"
              f"> historical usage change: {historical_usage} -> {updated_historical_usage}\n"
              f"> limit change: {current_limit} -> {updated_limit}")
