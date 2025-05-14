"""ORM for application specific database models.

Model objects are used to define the expected schema for individual database
tables and provide an object-oriented interface for executing database logic.
Each model reflects a different database and defines low-level defaults for how
the associated table/fields/records are presented by parent interfaces.
"""

from django.conf import settings
from django.db import models

__all__ = ['Notification', 'Preference']


def default_expiry_thresholds() -> list[int]:  # pragma: nocover
    """The default expiration thresholds at which to issue a user notification.

    Returned values are defined in units of days until expiration.
    """

    return [30, 14]


class Notification(models.Model):
    """User notification."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['time']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['user']),
            models.Index(fields=['user', 'read', 'notification_type']),
            models.Index(fields=['user', 'notification_type', 'time']),
        ]

    class NotificationType(models.TextChoices):
        """Enumerated choices for the `notification_type` field."""

        general_message = 'GM', 'General Message'
        request_expiring = 'RE', 'Upcoming Request Expiration'
        request_expired = 'RD', 'Request Past Expiration'

    time = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    subject = models.TextField()
    message = models.TextField()
    metadata = models.JSONField(null=True)
    notification_type = models.CharField(max_length=2, choices=NotificationType.choices)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Preference(models.Model):
    """User notification preferences."""

    class Meta:
        """Database model settings."""

        indexes = [
            models.Index(fields=['user']),
        ]

    request_expiry_thresholds = models.JSONField(default=default_expiry_thresholds)
    notify_on_expiration = models.BooleanField(default=True)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @classmethod
    def get_user_preference(cls, user: settings.AUTH_USER_MODEL) -> 'Preference':
        """Retrieve user preferences or create them if they don't exist."""

        preference, _ = cls.objects.get_or_create(user=user)
        return preference

    @classmethod
    def set_user_preference(cls, user: settings.AUTH_USER_MODEL, **kwargs) -> None:
        """Set user preferences, creating or updating as necessary."""

        cls.objects.update_or_create(user=user, defaults=kwargs)

    def get_expiration_threshold(self, days_until_expire: int) -> int | None:
        """Return the next threshold at which an expiration notification should be sent.

        The next notification occurs at the smallest threshold that is
        greater than or equal to the days until expiration.

        Args:
            days_until_expire: The number of days until an allocation expires.

        Returns:
            The next notification threshold in days, or `None` if none are met.
        """

        return min(
            filter(lambda x: x >= days_until_expire, self.request_expiry_thresholds),
            default=None
        )

    def get_usage_threshold(self, usage_percentage: int) -> int | None:
        """Return the next threshold at which a usage notification should be sent.

        The next notification occurs at the largest threshold that is
        less than or equal to the usage percentage.

        Args:
            usage_percentage: An allocation's percent utilization.

        Returns:
            The next notification threshold in percent, or `None` if none are met.
        """

        return max(
            filter(lambda x: x <= usage_percentage, self.request_expiry_thresholds),
            default=None
        )
