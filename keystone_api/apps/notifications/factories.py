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

from apps.users.factories import UserFactory
from .models import *

__all__ = ['NotificationFactory', 'PreferenceFactory']


class NotificationFactory(DjangoModelFactory):
    """Factory for creating mock `Notification` instances."""

    class Meta:
        """Factory settings."""

        model = Notification

    time = factory.Faker('date_time_this_year')
    read = factory.Faker("pybool", truth_probability=30)
    subject = factory.Faker('sentence', nb_words=6)
    message = factory.Faker('paragraph', nb_sentences=3)
    notification_type = randgen.choice(Notification.NotificationType.values)

    user = factory.SubFactory(UserFactory, is_staff=False)


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating mock `Preference` instances."""

    class Meta:
        """Factory settings."""

        model = Preference

    request_expiry_thresholds = factory.LazyFunction(lambda: [30, 14])
    notify_on_expiration = factory.Faker("pybool", truth_probability=75)

    user = factory.SubFactory(UserFactory, is_staff=False)
