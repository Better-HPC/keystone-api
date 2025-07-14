"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from factory.django import DjangoModelFactory
from factory.random import randgen

from .models import *

__all__ = ['MembershipFactory', 'TeamFactory', 'UserFactory']


class UserFactory(DjangoModelFactory):
    """Factory for creating mock `User` instances."""

    class Meta:
        """Factory settings."""

        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'password123!')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    department = factory.Faker('bs')
    role = factory.Faker('job')

    is_active = factory.Faker('pybool', truth_probability=0.98)
    is_staff = factory.Faker('pybool')
    is_ldap_user = False


class TeamFactory(DjangoModelFactory):
    """Factory for creating mock `Team` instances."""

    class Meta:
        """Factory settings."""

        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")
    is_active = True

    @factory.post_generation
    def users(self, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `users` relationship."""

        if extracted and not create:
            for user in extracted:
                self.users.add(user)


class MembershipFactory(DjangoModelFactory):
    """Factory for creating mock `Membership` instances."""

    class Meta:
        """Factory settings."""

        model = Membership

    role = randgen.choice(Membership.Role.values)

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
