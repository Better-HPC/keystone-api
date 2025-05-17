"""Function tests for the `/notifications/notifications/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.models import Notification
from apps.users.models import User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    """

    endpoint_pattern = '/notifications/notifications/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts from testing fixtures."""

        self.user1 = User.objects.get(username='owner_1')
        self.user1_notification = Notification.objects.get(user=self.user1)

        self.user2 = User.objects.get(username='owner_2')
        self.staff_user = User.objects.get(username='staff_user')

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        endpoint = self.endpoint_pattern.format(pk=self.user1.id)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_401_UNAUTHORIZED,
            head=status.HTTP_401_UNAUTHORIZED,
            options=status.HTTP_401_UNAUTHORIZED,
            post=status.HTTP_401_UNAUTHORIZED,
            put=status.HTTP_401_UNAUTHORIZED,
            patch=status.HTTP_401_UNAUTHORIZED,
            delete=status.HTTP_401_UNAUTHORIZED,
            trace=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_same_user(self) -> None:
        """Verify authenticated users can access and modify their own records."""

        # Define a user / record endpoint from the SAME user
        endpoint = self.endpoint_pattern.format(pk=self.user1_notification.id)
        self.client.force_authenticate(user=self.user1)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_user_different_user(self) -> None:
        """Verify users cannot modify other users' records."""

        # Define a user / record endpoint from a DIFFERENT user
        endpoint = self.endpoint_pattern.format(pk=self.user1_notification.id)
        self.client.force_authenticate(user=self.user2)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_404_NOT_FOUND,
            head=status.HTTP_404_NOT_FOUND,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        endpoint = self.endpoint_pattern.format(pk=self.user1_notification.id)
        self.client.force_authenticate(user=self.staff_user)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_404_NOT_FOUND,
            head=status.HTTP_404_NOT_FOUND,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN,
        )
