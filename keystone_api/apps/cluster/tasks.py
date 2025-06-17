"""Scheduled tasks executed in parallel by Celery.

Tasks are scheduled and executed in the background by Celery. They operate
asynchronously from the rest of the application and log their results in the
application database.
"""

from celery import shared_task

from apps.allocations.models import Cluster
from apps.cluster.models import JobStats
from apps.users.models import User
from plugins.slurm import get_cluster_jobs


@shared_task
def slurm_update_job_stats_for_cluster(cluster_id: int) -> None:
    """Fetch job statistics for a single cluster and update the DB."""

    cluster = Cluster.objects.get(pk=cluster_id)

    objs = []
    for job in get_cluster_jobs(cluster.name):
        job['username'] = job['user']
        job['user'] = User.objects.get_from_username(job['username'])
        objs.append(JobStats(**job))

    JobStats.objects.bulk_create(objs, update_conflicts=True)


@shared_task
def slurm_update_job_stats() -> None:
    """Fetch job statistics for all clusters and update the DB.

    Dispatches dedicated subtasks to update job statistics for each active
    cluster in the application database.
    """

    clusters = Cluster.objects.filter(enabled=True).values_list('id', flat=True)
    for cluster_id in clusters:
        slurm_update_job_stats_for_cluster.delay(cluster_id)
