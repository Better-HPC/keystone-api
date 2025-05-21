"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from django.template.defaultfilters import truncatechars

from apps.users.models import Team
from .managers import *

__all__ = ['Grant', 'Publication']


@auditlog.register()
class Grant(models.Model):
    """Metadata for a funding grant."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['agency']),
            models.Index(fields=['grant_number']),
            models.Index(fields=['fiscal_year']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['team']),
            models.Index(fields=['team', 'start_date', 'end_date']),
            models.Index(fields=['agency', 'start_date', 'end_date']),
            models.Index(fields=['team', 'agency', 'start_date', 'end_date']),
        ]

    title = models.CharField(max_length=250)
    agency = models.CharField(max_length=100)
    amount = models.DecimalField(decimal_places=2, max_digits=14)
    grant_number = models.CharField(max_length=250)
    fiscal_year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    history = AuditlogHistoryField()

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    objects = GrantManager()

    def __str__(self) -> str:  # pragma: nocover
        """Return the grant title truncated to 100 characters."""

        return truncatechars(self.title, 100)


@auditlog.register()
class Publication(models.Model):
    """Metadata for an academic publication."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['published']),
            models.Index(fields=['submitted']),
            models.Index(fields=['journal']),
            models.Index(fields=['doi']),
            models.Index(fields=['team']),
            models.Index(fields=['team', 'journal']),
            models.Index(fields=['team', 'published']),
            models.Index(fields=['team', 'submitted']),
        ]

    title = models.CharField(max_length=250)
    abstract = models.TextField()
    published = models.DateField(null=True, blank=True)
    submitted = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=100, null=True, blank=True)
    doi = models.CharField(max_length=50, unique=True, null=True, blank=True)
    preparation = models.BooleanField(default=False)
    volume = models.CharField(max_length=20, null=True, blank=True)
    issue = models.CharField(max_length=20, null=True, blank=True)
    history = AuditlogHistoryField()

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    objects = PublicationManager()

    def __str__(self) -> str:  # pragma: nocover
        """Return the publication title truncated to 100 characters."""

        return truncatechars(self.title, 100)
