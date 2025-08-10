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

    # Trigger a separate, concurrent background task for each cluster
    for cluster in Cluster.objects.filter(enabled=True).all():
        update_limits_for_cluster.delay(cluster.name)


@shared_task()
def update_limits_for_cluster(cluster_name: str) -> None:
    """Adjust TRES billing limits for all Slurm accounts on a given cluster.

    Any Slurm accounts without a corresponding Keystone team are ignored.
    The `root` account is also ignored.

    Args:
        cluster_name: The name of the Slurm cluster to update.
    """

    try:
        cluster = Cluster.objects.get(name=cluster_name)

    except Cluster.DoesNotExist:
        log.error(f"Cluster '{cluster_name}' does not exist.")
        return

    slurm_accounts = slurm.get_slurm_account_names(cluster.name)
    teams_by_name = {
        team.name: team for team in Team.objects.filter(name__in=slurm_accounts)
    }

    for account_name in slurm_accounts:
        if account_name == 'root':
            continue

        try:
            team = teams_by_name[account_name]

        except KeyError:
            log.warning(f"No existing team for account '{account_name}' on cluster '{cluster.name}'.")
            continue

        try:
            update_limit_for_account(team, cluster)

        except Exception as e:
            log.exception(f"Failed to update limit for account '{account_name}' on cluster '{cluster.name}': {e}")
            continue


def update_limit_for_account(account: Team, cluster: Cluster) -> None:
    """Update resource limits for an individual Slurm account.

    Args:
        account: Team object for the account.
        cluster: Cluster object corresponding to the Slurm cluster.
    """

    # Retrieve service units (SUs) associated with:
    # - active_sus: Total SUs across all currently active allocations
    # - expiring_sus: Total SUs about to expire
    active_sus = Allocation.objects.active_service_units(account, cluster)
    expiring_sus = Allocation.objects.expiring_service_units(account, cluster)

    # Get the current TRES limit from Slurm and use it to estimate
    # previously consumed SUs not tied to active/expiring allocations
    current_limit = slurm.get_cluster_limit(account.name, cluster.name)
    historical_usage = current_limit - active_sus - expiring_sus

    if historical_usage < 0:
        historical_usage = 0
        log.warning(
            f"Negative historical usage calculated for account '{account.name}' on cluster '{cluster.name}':\n"
            f"  > current limit: {current_limit}\n"
            f"  > active sus: {active_sus}\n"
            f"  > expiring sus: {expiring_sus}\n"
            f"  > historical usage: {historical_usage}\n"
            f"Assuming zero...")

    # Calculate consumed SUs attributable to current (non-expired) allocations
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

    # Distribute current usage across expiring allocations proportionally,
    # capping each at its awarded value and reducing remaining usage
    expired_allocations = Allocation.objects.expiring_allocations(account, cluster)
    for allocation in expired_allocations:
        allocation.final = min(current_usage, allocation.awarded)
        current_usage -= allocation.final

    Allocation.objects.bulk_update(expired_allocations, ['final'])

    # Sanity check: usage beyond the sum of active allocations may indicate a bug or abuse
    if current_usage > active_sus:
        log.warning(f"The system usage for account '{account.name}' exceeds its limit on cluster '{cluster.name}'")

    # Recalculate historical usage based on updated allocations, and set a new TRES limit in Slurm
    updated_historical_usage = Allocation.objects.historical_usage(account, cluster)
    updated_limit = updated_historical_usage + active_sus
    slurm.set_cluster_limit(account.name, cluster.name, updated_limit)

    log.debug(
        f"Setting new TRES limit for account '{account.name}' on cluster '{cluster.name}':\n"
        f"  > limit change: {current_limit} -> {updated_limit}")
