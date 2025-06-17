"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

from django.db import models

from apps.users.models import User

__all__ = ['JobStats']


class JobStats(models.Model):
    """Slurm Job status and statistics."""

    account = models.CharField(max_length=128, null=True, blank=True)
    alloc_nodes = models.CharField(max_length=128, null=True, blank=True)
    alloc_tres = models.TextField(null=True, blank=True)
    derived_exit_code = models.IntegerField(null=True, blank=True)
    elapsed = models.CharField(max_length=32, null=True, blank=True)  # e.g., "01:23:45"
    end = models.DateTimeField(null=True, blank=True)
    group = models.CharField(max_length=128, null=True, blank=True)
    job_id = models.CharField(max_length=64, unique=True)
    job_name = models.CharField(max_length=512, null=True, blank=True)
    node_list = models.TextField(null=True, blank=True)
    priority = models.IntegerField(null=True, blank=True)
    partition = models.CharField(max_length=128, null=True, blank=True)
    qos = models.CharField(max_length=128, null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=64, null=True, blank=True)
    submit = models.DateTimeField(null=True, blank=True)
    username = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        """Database model settings."""

        ordering = ["-submit"]
        indexes = [
            models.Index(fields=["job_id"]),
            models.Index(fields=["user"]),
            models.Index(fields=["state"]),
        ]
