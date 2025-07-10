"""Factories for creating test instances of Notification and Preference models.
These factories use the factory library to generate realistic data for testing purposes.
This module defines two factories: NotificationFactory and PreferenceFactory.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy

from apps.notifications.models import Notification, Preference
from apps.users.factories import UserFactory


class NotificationFactory(DjangoModelFactory):
    """Factory for creating test instances of a Notification model."""

    class Meta:
        model = Notification

    time = factory.Faker("date_time_this_year")
    read = factory.Faker("boolean", chance_of_getting_true=50)
    subject = factory.Faker("sentence", nb_words=6)
    message = factory.Faker("paragraph", nb_sentences=3)
    metadata = factory.LazyFunction(lambda: {"key": "value"})
    notification_type = fuzzy.FuzzyChoice(Notification.NotificationType.values)
    user = factory.SubFactory(UserFactory)


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating test instances of a Preference model."""

    class Meta:
        model = Preference

    request_expiry_thresholds = factory.LazyFunction(lambda: [30, 14])
    notify_on_expiration = factory.Faker("boolean", chance_of_getting_true=80)
    user = factory.SubFactory(UserFactory)
