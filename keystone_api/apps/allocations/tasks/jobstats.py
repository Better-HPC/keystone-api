"""Background tasks for synchronizing cached job statistics against Slurm."""

from celery import shared_task

from apps.allocations.models import Cluster, JobStats
from apps.users.models import Team
from plugins.slurm import get_cluster_jobs


@shared_task
def slurm_update_job_stats_for_cluster(cluster_id: int) -> None:
    """Fetch job statistics for a single cluster and update the DB."""

    # Fetch job information from slurm
    cluster = Cluster.objects.get(pk=cluster_id)
    cluster_jobs = get_cluster_jobs(cluster.name)

    # Prefetch team objects
    account_names = set(job['account'] for job in cluster_jobs)
    teams = Team.objects.filter(name__in=account_names)
    team_map = {team.name: team for team in teams}

    # Prepare JobStats objects
    objs = []
    for job in cluster_jobs:
        job['cluster'] = cluster
        job['username'] = job.pop('user', None)
        job['team'] = team_map.get(job['account'], None)
        objs.append(JobStats(**job))

    # Bulk insert, updating non-unique fields when unique fields have a conflict
    update_fields = [field.name for field in JobStats._meta.get_fields() if not field.unique]
    JobStats.objects.bulk_create(objs, update_conflicts=True, update_fields=update_fields)


@shared_task
def slurm_update_job_stats() -> None:
    """Fetch job statistics for all clusters and update the DB.

    Dispatches dedicated subtasks to update job statistics for each active
    cluster in the application database.
    """

    clusters = Cluster.objects.filter(enabled=True).values_list('id', flat=True)
    for cluster_id in clusters:
        slurm_update_job_stats_for_cluster.delay(cluster_id)
