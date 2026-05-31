"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database table and defines low-level defaults
for how the associated table/fields/records are presented by parent interfaces.
"""

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.contrib.auth import models as auth_models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.utils.text import slugify

from .managers import *

__all__ = ["Membership", "Team", "User"]


@auditlog.register()
class Membership(models.Model):
    """Relationship table between the `User` and `Team` models."""

    class Meta:
        """Database model settings."""

        constraints = [
            UniqueConstraint(fields=["user", "team"], name="unique_user_team")
        ]

        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["team", "role"]),
            models.Index(fields=["team", "user", "role"]),
        ]

    class Role(models.TextChoices):
        """Define choices for the `role` field.

        Roles are used to define user permissions within a team.
        """

        OWNER = "OW", "Owner"
        ADMIN = "AD", "Admin"
        MEMBER = "MB", "Member"

    role = models.CharField(max_length=2, choices=Role.choices)
    history = AuditlogHistoryField()

    user = models.ForeignKey("User", related_name="membership", on_delete=models.CASCADE)
    team = models.ForeignKey("Team", related_name="membership", on_delete=models.CASCADE)


@auditlog.register()
class Team(models.Model):
    """A collection of users who share resources and permissions."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["slug", "is_active"]),
        ]

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField("User", through=Membership)
    history = AuditlogHistoryField()

    objects = TeamManager()

    def get_all_members(self) -> models.QuerySet:
        """Return a queryset of all team members."""

        return self.users.all()

    def get_privileged_members(self) -> models.QuerySet:
        """Return a queryset of all team members with admin privileges."""

        return self.users.filter(membership__role__in=[
            Membership.Role.ADMIN,
            Membership.Role.OWNER
        ])

    def save(self, *args, **kwargs):
        """Persist the record to the database.

        When saving a record, the `slug` field is automatically updated to reflect
        the slugified value of the team name.
        """

        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: nocover
        """Return the team name."""

        return str(self.name)


@auditlog.register(exclude_fields=["last_login"], mask_fields=["password"])
class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    """Custom user model that extends the built-in Django `User`."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["first_name"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_staff"]),
            models.Index(fields=["is_ldap_user"]),
            models.Index(fields=["date_joined"]),
            models.Index(fields=["last_login"]),
            models.Index(fields=["is_active", "is_staff"]),
        ]

    # These values should always be defined when extending AbstractBaseUser
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    # User metadata
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator()])
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    department = models.CharField(max_length=1000, null=True, blank=True)
    role = models.CharField(max_length=1000, null=True, blank=True)
    history = AuditlogHistoryField()

    # Administrative values for user management/permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField("staff status", default=False)
    is_ldap_user = models.BooleanField("LDAP User", default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True)

    objects = UserManager()

    @property
    def display_name(self) -> str:
        """Return the user's display name."""

        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"

        return self.first_name or self.username

    @property
    def abbreviation(self) -> str:
        """Return the user's uppercase two-character abbreviation."""

        if self.first_name and self.last_name:
            abbrev = f"{self.first_name[0]}{self.last_name[0]}"

        elif self.first_name:
            abbrev = f"{self.first_name[0]}"

        else:
            abbrev = self.username[:2]

        return abbrev.upper()

    def get_all_teams(self) -> models.QuerySet:
        """Return a queryset containing all teams the user belongs to."""

        return Team.objects.filter(users=self)
