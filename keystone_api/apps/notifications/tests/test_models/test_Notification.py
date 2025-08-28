"""Unit tests for the `Notification` class."""

from django.db import IntegrityError
from django.test import TestCase

from apps.notifications.models import Notification
from apps.users.factories import UserFactory


class MetadataUniquenessConstraint(TestCase):
    """Verify the enforcement of uniqueness constraints on notification metadata.

    These tests ensure uniqueness constraints are designed to properly enforce the
    idempotence of user notifications. The enforcement of uniqueness constraints is
    ultimately left to the database / django ORM.
    """

    def test_prevents_duplicate_metadata(self) -> None:
        """Verify duplicate notifications for the same user, type, and identical metadata are rejected."""

        user = UserFactory()
        metadata = {"request_id": 1, "extra": "data"}

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 1",
            message="Test message 1",
            metadata=metadata
        )

        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                user=user,
                notification_type=Notification.NotificationType.request_expired,
                subject="Expired Duplicate",
                message="Test message duplicate",
                metadata=metadata
            )

    def test_allows_different_metadata(self) -> None:
        """Verify multiple notifications are allowed for the same user and type if metadata differs."""

        user = UserFactory()
        metadata1 = {"request_id": 1, "extra": "data"}
        metadata2 = {"request_id": 2, "extra": "data"}

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 1",
            message="Test message 1",
            metadata=metadata1
        )

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 2",
            message="Test message 2",
            metadata=metadata2
        )

        self.assertEqual(Notification.objects.count(), 2)

    def test_allows_subset_metadata(self) -> None:
        """Verify multiple notifications are allowed for the same user and type if the metadata is a proper subset."""

        user = UserFactory()
        metadata1 = {"request_id": 1, "extra": "data"}
        metadata2 = {"extra": "data"}

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 1",
            message="Test message 1",
            metadata=metadata1
        )

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 2",
            message="Test message 2",
            metadata=metadata2
        )

        self.assertEqual(Notification.objects.count(), 2)

    def test_allows_different_users_with_same_metadata(self) -> None:
        """Verify multiple notifications are allowed for the same type and metadata if the user is different."""

        user = UserFactory()
        other_user = UserFactory()
        metadata = {"request_id": 1, "extra": "data"}

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 1",
            message="Test message 1",
            metadata=metadata
        )

        Notification.objects.create(
            user=other_user,
            notification_type=Notification.NotificationType.request_expired,
            subject="Expired 2",
            message="Test message 2",
            metadata=metadata
        )

        self.assertEqual(Notification.objects.count(), 2)

    def test_allows_different_types_with_same_metadata(self) -> None:
        """Verify multiple notifications are allowed for the same user and metadata if the notification type is different."""

        user = UserFactory()
        metadata = {"request_id": 1, "extra": "data"}
        type1 = Notification.NotificationType.request_expired
        type2 = Notification.NotificationType.request_expiring

        Notification.objects.create(
            user=user,
            notification_type=type1,
            subject="Expired 1",
            message="Test message 1",
            metadata=metadata
        )

        Notification.objects.create(
            user=user,
            notification_type=type2,
            subject="Expired 2",
            message="Test message 2",
            metadata=metadata
        )

        self.assertEqual(Notification.objects.count(), 2)
