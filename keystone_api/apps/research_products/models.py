"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

from django.db import models
from django.template.defaultfilters import truncatechars

from apps.users.models import Team
from .managers import *

__all__ = ['Grant', 'Publication']


class Grant(models.Model):
    """Metadata for a funding grant."""

    title = models.CharField(max_length=250)
    agency = models.CharField(max_length=100)
    amount = models.DecimalField(decimal_places=2, max_digits=14)
    grant_number = models.CharField(max_length=250)
    fiscal_year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    objects = GrantManager()

    def __str__(self) -> str:  # pragma: nocover
        """Return the grant title truncated to 50 characters."""

        return truncatechars(self.title, 100)


class Publication(models.Model):
    """Metadata for an academic publication."""

    title = models.CharField(max_length=250)
    abstract = models.TextField()
    published = models.DateField(null=True, blank=True)
    submitted = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=100, null=True, blank=True)
    doi = models.CharField(max_length=50, unique=True, null=True, blank=True)
    preparation = models.BooleanField(default=False)
    volume = models.CharField(max_length=20, null=True, blank=True)
    issue = models.CharField(max_length=20, null=True, blank=True)

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    objects = PublicationManager()

    def __str__(self) -> str:  # pragma: nocover
        """Return the publication title truncated to 50 characters."""

        return truncatechars(self.title, 100)
