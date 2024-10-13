"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

import hashlib
import random
from io import BytesIO

from django.contrib.auth import models as auth_models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image

from .managers import *

__all__ = ['Team', 'TeamMembership', 'User']


class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    """Proxy model for the built-in django `User` model."""

    # These values should always be defined when extending AbstractBaseUser
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    # User metadata
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator()])
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=150, null=True)
    last_name = models.CharField(max_length=150, null=True)
    email = models.EmailField(null=True)
    department = models.CharField(max_length=1000, null=True, blank=True)
    role = models.CharField(max_length=1000, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    # Administrative values for user management/permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField('staff status', default=False)
    is_ldap_user = models.BooleanField('LDAP User', default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True)

    objects = UserManager()

    def _generate_default_image(self, grid_size: tuple[int, int] = (6, 6), square_size: int = 40) -> Image:
        """Generate a unique user profile image

        Generated images are a random color grid of NxM blocks, where the dimensions
        are determined by the `grid_size` argument.

        Args:
            grid_size: The size of the grid generated in the image
            square_size: The size of each grid square in pixels

        Returns:
            An RGB image
        """

        seed = int(hashlib.sha256(self.username.encode()).hexdigest(), 16)
        random.seed(seed)

        rgb_white = (255, 255, 255)
        image = Image.new('RGB', (grid_size[0] * square_size, grid_size[1] * square_size), rgb_white)

        random_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for i in range(grid_size[0]):
            for j in range(grid_size[1]):
                if random.choice([True, False]):
                    for x in range(square_size):
                        for y in range(square_size):
                            image.putpixel((i * square_size + x, j * square_size + y), random_color)

        return image

    def save(self, *args, **kwargs) -> None:
        """Persist the ORM instance to the database"""

        # Generate a profile image if one does not exist
        if not self.profile_image:
            image = self._generate_default_image()
            image_io = BytesIO()
            image.save(image_io, format='PNG')
            self.profile_image.save(f'{self.username}.png', ContentFile(image_io.getvalue()), save=False)

        super().save(*args, **kwargs)


class Team(models.Model):
    """A collection of users who share resources and permissions."""

    name = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(User, through='TeamMembership')
    is_active = models.BooleanField(default=True)

    objects = TeamManager()

    def get_all_members(self) -> models.QuerySet:
        """Return a queryset of all team members."""

        return self.users

    def get_privileged_members(self) -> models.QuerySet:
        """Return a queryset of all team with admin privileges."""

        return self.users.filter(teammembership__role__in=[
            TeamMembership.Role.ADMIN,
            TeamMembership.Role.OWNER
        ])

    def __str__(self) -> str:  # pragma: nocover
        """Return the team's account name."""

        return str(self.name)


class TeamMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = 'OW', 'Owner'
        ADMIN = 'AD', 'Admin'
        MEMBER = 'MB', 'Member'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=2, choices=Role.choices)

    class Meta:
        unique_together = ('user', 'team')
