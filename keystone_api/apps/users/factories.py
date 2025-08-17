"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from factory import LazyFunction
from factory.django import DjangoModelFactory
from factory.random import randgen

from .models import *

__all__ = ['MembershipFactory', 'TeamFactory', 'UserFactory']

# Using a fixed, prehashed password avoids the significant overhead
# of hashing a dynamically generated value for each record
DEFAULT_PASSWORD = make_password('password')


class TeamFactory(DjangoModelFactory):
    """Factory for creating mock `Team` instances."""

    class Meta:
        """Factory settings."""

        model = Team

    name = factory.Sequence(lambda n: f"Team {n + 1}")
    is_active = True

    @factory.post_generation
    def users(self: Team, create: bool, extracted: list[User] | None, **kwargs) -> None:
        """Populate the many-to-many `users` relationship."""

        if extracted and not create:
            for user in extracted:
                self.users.add(user)


class UserFactory(DjangoModelFactory):
    """Factory for creating mock `User` instances.

    Users are generated with a `date joined` within the last five years.
    """

    class Meta:
        """Factory settings."""

        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n + 1}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    department = factory.Faker('bs')
    role = factory.Faker('job')

    is_active = True
    is_staff = False
    is_ldap_user = False

    date_joined = factory.Faker('date_time_between', start_date='-5y', end_date='now', tzinfo=timezone.get_default_timezone())

    @factory.post_generation
    def password(self: User, create, extracted, **kwargs) -> None:
        """Hashes the user password before persisting the value."""

        if extracted is not None:
            self.password = make_password(extracted)

        else:
            self.password = DEFAULT_PASSWORD

        if create:
            self.save()


class MembershipFactory(DjangoModelFactory):
    """Factory for creating mock `Membership` instances."""

    class Meta:
        """Factory settings."""

        model = Membership

    role = LazyFunction(lambda: randgen.choice(Membership.Role.values))

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
