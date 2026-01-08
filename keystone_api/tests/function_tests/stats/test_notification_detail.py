"""Function tests for the `stats:notification-detail` endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.factories import NotificationFactory
from apps.users.factories import UserFactory
from tests.function_tests.utils import CustomAsserts

VIEW_NAME = 'stats:notification-detail'


class EndpointPermissions(CustomAsserts, APITestCase):
    """Test endpoint user permissions."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory()

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_permissions(self) -> None:
        """Verify authenticated users have read only permissions."""

        self.client.force_login(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class UserRecordFiltering(APITestCase):
    """Test returned metrics are filtered by user ownership."""

    endpoint = reverse(VIEW_NAME)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.user_1 = UserFactory()
        self.user_1_records = [
            NotificationFactory(user=self.user_1),
            NotificationFactory(user=self.user_1, read=False)
        ]

        self.user_2 = UserFactory()
        self.user_2_records = [
            NotificationFactory(user=self.user_2) for _ in range(4)
        ]

        self.staff_user = UserFactory(is_staff=True)
        self.all_records = self.user_1_records + self.user_2_records

    def test_generic_user_statistics(self) -> None:
        """Verify general users are only returned statistics for their own notifications."""

        self.client.force_authenticate(self.user_1)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.user_1_records), stats["total"])

    def test_staff_user_statistics(self) -> None:
        """Verify staff users are returned aggregated statistics across all users."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint)

        stats = response.json()
        self.assertEqual(len(self.all_records), stats["total"])

    def test_user_filtered_statistics(self) -> None:
        """Verify query values can be used to filter returned statistics by user."""

        self.client.force_authenticate(self.staff_user)
        response = self.client.get(self.endpoint, query_params={"user": self.user_1.id})

        stats = response.json()
        self.assertEqual(len(self.user_1_records), stats["total"])
