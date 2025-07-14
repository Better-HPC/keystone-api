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
from faker import Faker

from .models import *

__all__ = ['MembershipFactory', 'TeamFactory', 'UserFactory']

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating mock `User` instances."""

    class Meta:
        """Factory settings."""

        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'password123!')
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    department = factory.LazyAttribute(lambda _: fake.bs())
    role = factory.LazyAttribute(lambda _: fake.job())

    is_active = True
    is_staff = factory.LazyFunction(lambda: randgen.choice([True, False]))
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
        """Populate the many-to-many relationship with `User` instances."""

        if extracted and not create:
            for user in extracted:
                self.users.add(user)


class MembershipFactory(DjangoModelFactory):
    """Factory for creating mock `Membership` instances."""

    class Meta:
        """Factory settings."""

        model = Membership

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    role = randgen.choice([choice[0] for choice in Membership.Role.choices])
