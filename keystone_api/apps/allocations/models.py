"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database table and defines low-level defaults
for how the associated table/fields/records are presented by parent interfaces.
"""

import os
from abc import abstractmethod

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils import timezone

from apps.allocations.managers import ResourceAllocationManager
from apps.research_products.models import Grant, Publication
from apps.users.models import Team, User

__all__ = [
    "AllocationRequest",
    "AllocationReview",
    "Attachment",
    "Cluster",
    "Comment",
    "ResourceAllocation",
    "TeamModelInterface",
]


class TeamModelInterface:
    """Interface class for database models affiliated with a team."""

    @abstractmethod
    def get_team(self) -> Team:
        """Return the team associated with the current record."""


@auditlog.register()
class ResourceAllocation(TeamModelInterface, models.Model):
    """User service unit allocation.

    Allocations are marked as "expired" when their `final` field is populated.
    If this field is `None`, the allocation has not yet been processed as "expired".
    """

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["request"]),
            models.Index(fields=["cluster", "request"]),
        ]

    requested = models.PositiveIntegerField()
    awarded = models.PositiveIntegerField(null=True, blank=True)
    final = models.PositiveIntegerField(null=True, blank=True)
    history = AuditlogHistoryField()

    cluster = models.ForeignKey("Cluster", on_delete=models.PROTECT, related_name="allocation_set")
    request = models.ForeignKey("AllocationRequest", on_delete=models.CASCADE, related_name="allocation_set")

    objects = ResourceAllocationManager()

    def get_team(self) -> Team:
        """Return the user team tied to the current record."""

        return self.request.team

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Resource Allocation #{self.pk} - {self.cluster} allocation for {self.request.team}"


@auditlog.register()
class AllocationRequest(TeamModelInterface, models.Model):
    """User request for additional service units on one or more clusters."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["submitted"]),
            models.Index(fields=["active"]),
            models.Index(fields=["expire"]),
            models.Index(fields=["submitter"]),
            models.Index(fields=["team", "status"]),
            models.Index(fields=["team", "submitter", "status"]),
            models.Index(fields=["team", "active", "expire"]),
            models.Index(fields=["team", "expire"]),
            models.Index(fields=["submitter", "status"]),
        ]

    class StatusChoices(models.TextChoices):
        """Enumerated choices for the `status` field."""

        PENDING = "PD", "Pending"
        APPROVED = "AP", "Approved"
        DECLINED = "DC", "Declined"
        CHANGES = "CR", "Changes Requested"

    title = models.CharField(max_length=250)
    description = models.TextField(max_length=20_000)
    submitted = models.DateTimeField(default=timezone.now)
    active = models.DateField(null=True, blank=True)
    expire = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    history = AuditlogHistoryField()

    submitter = models.ForeignKey(User, on_delete=models.PROTECT, related_name="submitted_allocationrequest_set")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    assignees = models.ManyToManyField(User, blank=True, related_name="assigned_allocationrequest_set")
    publications = models.ManyToManyField(Publication, blank=True)
    grants = models.ManyToManyField(Grant, blank=True)

    def clean(self) -> None:
        """Validate the model instance.

        Raises:
            ValidationError: When the model instance data is not valid.
        """

        if self.active and self.expire and self.active >= self.expire:
            raise ValidationError("The expiration date must come after the activation date.")

    def get_team(self) -> Team:
        """Return the user team tied to the current record."""

        return self.team

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Allocation Request #{self.pk} - '{truncatechars(self.title, 100)}' for {self.team}"


@auditlog.register()
class AllocationReview(TeamModelInterface, models.Model):
    """Reviewer feedback for an allocation request."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["submitted"]),
            models.Index(fields=["request"]),
            models.Index(fields=["reviewer"]),
        ]

    class StatusChoices(models.TextChoices):
        """Enumerated choices for the `status` field."""

        APPROVED = "AP", "Approved"
        DECLINED = "DC", "Declined"
        CHANGES = "CR", "Changes Requested"

    status = models.CharField(max_length=2, choices=StatusChoices.choices)
    submitted = models.DateTimeField(default=timezone.now)
    history = AuditlogHistoryField()

    request = models.ForeignKey(AllocationRequest, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_team(self) -> Team:
        """Return the user team tied to the current record."""

        return self.request.team

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Allocation Review #{self.pk} - {self.reviewer.username} review of request #{self.request_id}"


@auditlog.register()
class Attachment(TeamModelInterface, models.Model):
    """File data uploaded by users."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["uploaded"]),
            models.Index(fields=["request"]),
        ]

    file = models.FileField(upload_to="allocations")
    name = models.CharField(max_length=250, blank=True)
    uploaded = models.DateTimeField(auto_now=True)
    history = AuditlogHistoryField()

    request = models.ForeignKey("AllocationRequest", on_delete=models.CASCADE)

    def get_team(self) -> Team:
        """Return the user team tied to the current record."""

        return self.request.team

    def save(self, *args, **kwargs) -> None:
        """Persist the ORM instance to the database.

        Defaults the `name` field to the uploaded file's base name.
        """

        # Set the default name to match the file path
        if not self.name:
            self.name = os.path.basename(self.file.path)

        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Attachment #{self.pk} - '{self.name}' on request #{self.request_id}"


@auditlog.register()
class Cluster(models.Model):
    """A Slurm cluster and its associated management settings."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["name"]),
        ]

    class AccessModeChoices(models.TextChoices):
        """Enumerated choices for the `access_mode` field."""

        WHITELIST = "WL", "Whitelist"
        BLACKLIST = "BL", "Blacklist"
        OPEN = "OP", "Open"

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=150, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    access_mode = models.CharField(max_length=2, choices=AccessModeChoices.choices, default=AccessModeChoices.OPEN)

    access_teams = models.ManyToManyField(Team, blank=True)

    history = AuditlogHistoryField()

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Cluster #{self.pk} - {self.name}"


@auditlog.register()
class Comment(TeamModelInterface, models.Model):
    """Comment associated with an allocation request."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["created"]),
            models.Index(fields=["request"]),
            models.Index(fields=["user", "request", "created"]),
        ]

    content = models.TextField(max_length=2_000)
    created = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)
    history = AuditlogHistoryField()

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    request = models.ForeignKey("AllocationRequest", on_delete=models.CASCADE, related_name="comments")

    def get_team(self) -> Team:
        """Return the user team tied to the current record."""

        return self.request.team

    def __str__(self) -> str:  # pragma: nocover
        """Return a human-readable identifier for the record."""

        return f"Comment #{self.pk} - by {self.user.username} on request #{self.request_id}"
