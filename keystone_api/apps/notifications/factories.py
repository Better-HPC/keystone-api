"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import date

import factory
from factory import LazyFunction
from factory.django import DjangoModelFactory
from factory.random import randgen

from apps.notifications.shortcuts import format_template, get_template
from apps.users.factories import UserFactory
from .models import *

__all__ = ['NotificationFactory', 'PreferenceFactory']

# Template context for expiring allocation notifications
_EXPIRING_TEMPLATE_CONTEXT = {
    'user_name': "jsmith",
    'user_first': "John",
    'user_last': "Smith",
    'req_id': 1234,
    'req_title': "Project Title",
    'req_team': "Team Name",
    'req_submitted': date(2024, 1, 1),
    'req_active': date(2024, 1, 8),
    'req_expire': date(2024, 12, 31),
    'req_days_left': 7,
    'allocations': (
        {'alloc_cluster': "Cluster 1", 'alloc_requested': 100_000, 'alloc_awarded': 100_000},
        {'alloc_cluster': "Cluster 2", 'alloc_requested': 250_000, 'alloc_awarded': 200_000},
    ),
}

# Template context for expired allocation notifications
_EXPIRED_TEMPLATE_CONTEXT = {
    'user_name': "jsmith",
    'user_first': "John",
    'user_last': "Smith",
    'req_id': 1234,
    'req_title': "Project Title",
    'req_team': "Team Name",
    'req_submitted': date(2024, 1, 1),
    'req_active': date(2024, 1, 8),
    'req_expire': date(2024, 12, 31),
    'allocations': (
        {'alloc_cluster': "Cluster 1", 'alloc_requested': 100_000, 'alloc_awarded': 100_000, 'alloc_final': 50_000},
        {'alloc_cluster': "Cluster 2", 'alloc_requested': 250_000, 'alloc_awarded': 200_000, 'alloc_final': 175_000},
    ),
}


class NotificationFactory(DjangoModelFactory):
    """Factory for creating mock `Notification` instances."""

    class Meta:
        model = Notification

    time = factory.Faker('date_time_this_year')
    read = factory.Faker("pybool", truth_probability=30)
    notification_type = LazyFunction(lambda: randgen.choice(Notification.NotificationType.values))
    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def subject(self) -> str:
        """Generate a subject line for the current notification.

        Returns:
            A subject string appropriate for the notification type.
        """

        match self.notification_type:
            case Notification.NotificationType.request_expired:
                return "Your HPC allocation 1234 has expired"

            case Notification.NotificationType.request_expiring:
                return "Your HPC allocation 1234 is expiring soon"

            case Notification.NotificationType.general_message:
                return "General notification"

            case _:
                raise RuntimeError(f"No factory support for notification type {self.notification_type}")

    @factory.lazy_attribute
    def message(self) -> str:
        """Generate a message body based on the notification type.

        Returns:
            The notification message content.
        """

        match self.notification_type:
            case Notification.NotificationType.request_expired:
                template = get_template("past_expiration.html")
                html_content, _ = format_template(template, context=_EXPIRED_TEMPLATE_CONTEXT)
                return html_content

            case Notification.NotificationType.request_expiring:
                template = get_template("upcoming_expiration.html")
                html_content, _ = format_template(template, context=_EXPIRING_TEMPLATE_CONTEXT)
                return html_content

            case Notification.NotificationType.general_message:
                return "This is a general notification message."

            case _:
                raise RuntimeError(f"No factory support for notification type {self.notification_type}")


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating mock `Preference` instances."""

    class Meta:
        """Factory settings."""

        model = Preference

    request_expiry_thresholds = factory.LazyFunction(default_expiry_thresholds)
    notify_on_expiration = True

    user = factory.SubFactory(UserFactory)
