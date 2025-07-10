"""Factory classes for creating test data for User, Team, and Membership models.

These factories use the factory library to generate realistic data for testing purposes.
The UserFactory creates users with random usernames, emails, and other attributes.
The TeamFactory creates teams with random names and can associate users with teams.
The MembershipFactory creates membership records linking users to teams with specified roles.
"""

import random
import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory import fuzzy
from faker import Faker

from .models import User, Team, Membership

fake = Faker()

class UserFactory(DjangoModelFactory):
    """Factory for creating test instances of a User model."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    department = factory.LazyAttribute(lambda _: fake.bs())
    role = factory.LazyAttribute(lambda _: fake.job())
    is_active = True
    is_staff = factory.LazyFunction(lambda: random.choice([True, False]))
    is_ldap_user = False
    date_joined = factory.LazyFunction(timezone.now)
    last_login = factory.LazyFunction(timezone.now)


class TeamFactory(DjangoModelFactory):
    """Factory for creating test instances of a Team model."""

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
    """Factory for creating test instances of a Membership model."""

    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    role = fuzzy.FuzzyChoice([choice[0] for choice in Membership.Role.choices])
