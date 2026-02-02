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

__all__ = ["NotificationFactory", "PreferenceFactory"]

# Template context for general notifications
_GENERAL_TEMPLATE_CONTEXT = {
    "user_name": "jsmith",
    "user_first": "John",
    "user_last": "Smith",
    "message": "This is an important general notification concerning your HPC account."
}

# Template context for expiring allocation notifications
_EXPIRING_TEMPLATE_CONTEXT = {
    "user_name": "jsmith",
    "user_first": "John",
    "user_last": "Smith",
    "req_id": 1234,
    "req_title": "Project Title",
    "req_team": "Team Name",
    "req_submitted": date(2024, 1, 1),
    "req_active": date(2024, 1, 8),
    "req_expire": date(2024, 12, 31),
    "req_days_left": 7,
    "allocations": (
        {"alloc_cluster": "Cluster 1", "alloc_requested": 100_000, "alloc_awarded": 100_000},
        {"alloc_cluster": "Cluster 2", "alloc_requested": 250_000, "alloc_awarded": 200_000},
    ),
}

# Template context for expired allocation notifications
_EXPIRED_TEMPLATE_CONTEXT = {
    "user_name": "jsmith",
    "user_first": "John",
    "user_last": "Smith",
    "req_id": 1234,
    "req_title": "Project Title",
    "req_team": "Team Name",
    "req_submitted": date(2024, 1, 1),
    "req_active": date(2024, 1, 8),
    "req_expire": date(2024, 12, 31),
    "allocations": (
        {"alloc_cluster": "Cluster 1", "alloc_requested": 100_000, "alloc_awarded": 100_000, "alloc_final": 50_000},
        {"alloc_cluster": "Cluster 2", "alloc_requested": 250_000, "alloc_awarded": 200_000, "alloc_final": 175_000},
    ),
}


class NotificationFactory(DjangoModelFactory):
    """Factory for creating mock `Notification` instances."""

    class Meta:
        model = Notification

    time = factory.Faker("date_time_this_year")
    read = factory.Faker("pybool", truth_probability=30)
    notification_type = LazyFunction(lambda: randgen.choice(Notification.NotificationType.values))
    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def subject(self) -> str:
        """Generate a subject line for the current notification."""

        match self.notification_type:
            case Notification.NotificationType.request_expired:
                return "Your HPC allocation 1234 has expired"

            case Notification.NotificationType.request_expiring:
                return "Your HPC allocation 1234 is expiring soon"

            case Notification.NotificationType.general_message:
                return "General notification"

            case _:
                raise RuntimeError(f"No subject factory support for notification type {self.notification_type}")

    @factory.lazy_attribute
    def message_html(self) -> str:
        """Generate an HTML message body based on the notification type."""

        html_content, _ = self._render_template()
        return html_content

    @factory.lazy_attribute
    def message_text(self) -> str:
        """Generate a plain text message body based on the notification type."""

        _, text_content = self._render_template()
        return text_content

    def _render_template(self) -> tuple[str, str]:
        """Render the template for the current notification type.

        Returns:
            A tuple of containing the rendered notification in (html, plain_text) format.
        """

        match self.notification_type:
            case Notification.NotificationType.request_expired:
                template_name = "past_expiration.html"
                context = _EXPIRED_TEMPLATE_CONTEXT

            case Notification.NotificationType.request_expiring:
                template_name = "upcoming_expiration.html"
                context = _EXPIRING_TEMPLATE_CONTEXT

            case Notification.NotificationType.general_message:
                template_name = "general.html"
                context = _GENERAL_TEMPLATE_CONTEXT

            case _:
                raise RuntimeError(f"No message factory support for notification type {self.notification_type}")

        template = get_template(template_name)
        return format_template(template, context=context)


class PreferenceFactory(DjangoModelFactory):
    """Factory for creating mock `Preference` instances."""

    class Meta:
        """Factory settings."""

        model = Preference

    request_expiry_thresholds = factory.LazyFunction(default_expiry_thresholds)
    notify_on_expiration = True

    user = factory.SubFactory(UserFactory)
