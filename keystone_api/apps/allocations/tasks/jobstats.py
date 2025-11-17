"""Background tasks for synchronizing cached job statistics against Slurm."""

from celery import shared_task

from apps.allocations.models import Cluster, Job
from apps.users.models import Team
from plugins.slurm import get_cluster_jobs

__all__ = [
    'slurm_update_job_stats',
    'slurm_update_job_stats_for_cluster',
]


@shared_task
def slurm_update_job_stats() -> None:
    """Fetch job statistics for all clusters and update the DB.

    Dispatches dedicated subtasks to update job statistics for each active
    cluster in the application database.
    """

    clusters = Cluster.objects.filter(enabled=True).values_list('name', flat=True)
    for cluster_name in clusters:
        slurm_update_job_stats_for_cluster.delay(cluster_name)


@shared_task
def slurm_update_job_stats_for_cluster(cluster_name: str) -> None:
    """Fetch job statistics for a single cluster and update the DB.

    Args:
        cluster_name: The name of the slurm cluster to update.
    """

    # Fetch job information from slurm
    cluster = Cluster.objects.get(name=cluster_name)
    cluster_jobs = get_cluster_jobs(cluster.name)

    # Prefetch team objects from the database
    account_names = set(job['account'] for job in cluster_jobs)
    teams = Team.objects.filter(name__in=account_names)
    team_map = {team.name: team for team in teams}

    # Map Slurm fields to model fields
    objs = []
    for job_data in cluster_jobs:
        objs.append(
            Job(**{
                'jobid': job_data.get('jobid'),
                'jobname': job_data.get('jobname'),
                'account': job_data.get('account'),
                'username': job_data.get('user'),
                'submit': job_data.get('submit'),
                'start': job_data.get('start'),
                'end': job_data.get('end'),
                'state': job_data.get('state'),
                'exit_code': job_data.get('derivedexitcode'),
                'priority': job_data.get('priority'),
                'qos': job_data.get('qos'),
                'nodes': job_data.get('allocnodes'),
                'partition': job_data.get('partition'),
                'sus': job_data.get('alloctres'),
                'team': team_map.get(job_data.get('account')),
                'cluster': cluster,
            })
        )

    # Bulk insert/update
    update_fields = [field.name for field in Job._meta.get_fields() if not field.unique]
    Job.objects.bulk_create(objs, update_conflicts=True, unique_fields=['jobid'], update_fields=update_fields)
