"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy

from .models import *
from apps.users.factories import UserFactory
from apps.factories.providers import global_provider


class NotificationFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Notification` model."""

    class Meta:
        model = Notification

    time = factory.LazyFunction(lambda: global_provider.fake.date_time_this_year())
    read = factory.LazyFunction(lambda: global_provider.fake.boolean(chance_of_getting_true=30))
    subject = factory.LazyFunction(lambda: global_provider.fake.sentence(nb_words=6))
    message = factory.LazyFunction(lambda: global_provider.fake.paragraph(nb_sentences=3))
    metadata = factory.LazyFunction(lambda: {"key": "value"})
    notification_type = fuzzy.FuzzyChoice(Notification.NotificationType.values)
    user = factory.SubFactory(UserFactory)


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Preference` model."""

    class Meta:
        model = Preference

    request_expiry_thresholds = factory.LazyFunction(lambda: [30, 14])
    notify_on_expiration = factory.LazyFunction(lambda: global_provider.fake.boolean(chance_of_getting_true=75))
    user = factory.SubFactory(UserFactory)
