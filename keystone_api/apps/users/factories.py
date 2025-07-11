"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory import fuzzy

from apps.factories.providers import global_provider
from .models import *

class UserFactory(DjangoModelFactory):
    """Factory for creating test instances of a `User` model."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    first_name = factory.LazyAttribute(lambda _: global_provider.fake.first_name())
    last_name = factory.LazyAttribute(lambda _: global_provider.fake.last_name())
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    department = factory.LazyAttribute(lambda _: global_provider.fake.bs())
    role = factory.LazyAttribute(lambda _: global_provider.fake.job())
    is_active = True
    is_staff = factory.LazyFunction(lambda: global_provider.random.choice([True, False]))
    is_ldap_user = False
    date_joined = factory.LazyFunction(timezone.now)
    last_login = factory.LazyFunction(timezone.now)


class TeamFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Team` model."""

    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")
    is_active = True

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.users.add(user)


class MembershipFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Membership` model."""

    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    role = fuzzy.FuzzyChoice([choice[0] for choice in Membership.Role.choices])
