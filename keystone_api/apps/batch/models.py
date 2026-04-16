"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database table and defines low-level defaults
for how the associated table/fields/records are presented by parent interfaces.
"""

import uuid

from django.db import models

__all__ = ['JobStatus']


class JobStatus(models.Model):
    """A batch job and its execution status."""

    class Status(models.TextChoices):
        """Enumerated choices for the `status` field."""

        CREATED = 'CR', 'Created'
        SUCCEEDED = 'SC', 'Succeeded'
        FAILED = 'FL', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=2, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    error_detail = models.TextField(blank=True, default='')
