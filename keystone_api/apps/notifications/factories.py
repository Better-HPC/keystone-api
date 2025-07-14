"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker

from apps.users.factories import UserFactory
from .models import *

fake = Faker()


class NotificationFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Notification` model."""

    class Meta:
        model = Notification

    time = factory.LazyFunction(lambda: fake.date_time_this_year())
    read = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=30))
    subject = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    message = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))
    metadata = factory.LazyFunction(lambda: {"key": "value"})
    notification_type = fuzzy.FuzzyChoice(Notification.NotificationType.values)
    user = factory.SubFactory(UserFactory)


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Preference` model."""

    class Meta:
        model = Preference

    request_expiry_thresholds = factory.LazyFunction(lambda: [30, 14])
    notify_on_expiration = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=75))
    user = factory.SubFactory(UserFactory)
