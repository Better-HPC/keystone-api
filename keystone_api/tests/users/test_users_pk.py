"""Function tests for the `/users/users/<pk>/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 403 | 403  | 403     | 403  | 403 | 403   | 403    | 403   |
    | User accessing own account | 200 | 200  | 200     | 403  | 200 | 200   | 204    | 405   |
    | User accessing other user  | 200 | 200  | 200     | 403  | 403 | 403   | 403    | 405   |
    | Staff user                 | 200 | 200  | 200     | 405  | 200 | 200   | 204    | 405   |
    """

    endpoint_pattern = '/users/users/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts from testing fixtures."""

        self.user1 = User.objects.get(username='member_1')
        self.user2 = User.objects.get(username='member_2')
        self.staff_user = User.objects.get(username='staff_user')

    def test_unauthenticated_user_permissions(self) -> None:
        """Verify unauthenticated users cannot access resources."""

        endpoint = self.endpoint_pattern.format(pk=self.user1.id)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_403_FORBIDDEN,
            head=status.HTTP_403_FORBIDDEN,
            options=status.HTTP_403_FORBIDDEN,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_403_FORBIDDEN
        )

    def test_authenticated_user_same_user(self) -> None:
        """Verify authenticated users can access and modify their own records."""

        # Define a user / record endpoint from the SAME user
        endpoint = self.endpoint_pattern.format(pk=self.user1.id)
        self.client.force_authenticate(user=self.user1)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={
                'username': 'foobar',
                'password': 'foobar123',
                'first_name': 'Foo',
                'last_name': 'Bar',
                'email': 'foo@bar.com'},
            patch_body={'email': 'member_3@newdomain.com'},
        )

    def test_authenticated_user_different_user(self) -> None:
        """Verify users cannot modify other users' records."""

        # Define a user / record endpoint from a DIFFERENT user
        endpoint = self.endpoint_pattern.format(pk=self.user1.id)
        self.client.force_authenticate(user=self.user2)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_403_FORBIDDEN,
            patch=status.HTTP_403_FORBIDDEN,
            delete=status.HTTP_403_FORBIDDEN,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users have full read and write permissions."""

        endpoint = self.endpoint_pattern.format(pk=self.user1.id)
        self.client.force_authenticate(user=self.staff_user)

        self.assert_http_responses(
            endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_405_METHOD_NOT_ALLOWED,
            put=status.HTTP_200_OK,
            patch=status.HTTP_200_OK,
            delete=status.HTTP_204_NO_CONTENT,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            put_body={
                'username': 'foobar',
                'password': 'foobar123',
                'first_name': 'Foo',
                'last_name': 'Bar',
                'email': 'foo@bar.com'},
            patch_body={'email': 'foo@bar.com'},
        )


class CredentialHandling(APITestCase):
    """Test the getting/setting of user credentials."""

    endpoint_pattern = '/users/users/{pk}/'
    fixtures = ['testing_common.yaml']

    def setUp(self) -> None:
        """Load user accounts from testing fixtures."""

        self.user1 = User.objects.get(username='member_1')
        self.user2 = User.objects.get(username='member_2')
        self.staff_user = User.objects.get(username='staff_user')

    def test_user_get_own_password(self) -> None:
        """Verify users cannot retrieve their own password."""

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            self.endpoint_pattern.format(pk=self.user1.id)
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotIn('password', response.json())

    def test_user_set_own_password(self) -> None:
        """Verify users can change their own password."""

        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            path=self.endpoint_pattern.format(pk=self.user1.id),
            data={'password': 'new_password123'}
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('new_password123'))

    def test_user_get_others_password(self) -> None:
        """Verify users cannot retrieve another user's password."""

        authenticated_user = self.user1
        other_user = self.user2
        self.client.force_authenticate(user=authenticated_user)

        response = self.client.get(
            self.endpoint_pattern.format(pk=other_user.id),
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotIn('password', response.data)

    def test_user_set_others_password(self) -> None:
        """Verify users cannot change another user's password."""

        authenticated_user = self.user1
        other_user = self.user2
        self.client.force_authenticate(user=authenticated_user)

        response = self.client.patch(
            path=self.endpoint_pattern.format(pk=other_user.id),
            data={'password': 'new_password123'}
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_staff_get_password(self) -> None:
        """Verify staff users cannot retrieve user passwords."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            self.endpoint_pattern.format(pk=self.user1.id)
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotIn('password', response.json())

    def test_staff_set_password(self) -> None:
        """Verify staff users can change user passwords."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(
            path=self.endpoint_pattern.format(pk=self.user1.id),
            data={'password': 'new_password123'}
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password('new_password123'))
