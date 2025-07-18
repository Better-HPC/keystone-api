"""Function tests for the `/users/users/` endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory
from apps.users.models import User
from tests.utils import CustomAsserts


class EndpointPermissions(APITestCase, CustomAsserts):
    """Test endpoint user permissions.

    Endpoint permissions are tested against the following matrix of HTTP responses.

    | User Status                | GET | HEAD | OPTIONS | POST | PUT | PATCH | DELETE | TRACE |
    |----------------------------|-----|------|---------|------|-----|-------|--------|-------|
    | Unauthenticated user       | 401 | 401  | 401     | 401  | 401 | 401   | 401    | 401   |
    | Authenticated user         | 200 | 200  | 200     | 403  | 405 | 405   | 405    | 405   |
    | Staff user                 | 200 | 200  | 200     | 201  | 405 | 405   | 405    | 405   |
    """

    endpoint = '/users/users/'

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

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
        """Verify authenticated can read user info."""

        self.client.force_authenticate(user=self.generic_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_403_FORBIDDEN,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_staff_user_permissions(self) -> None:
        """Verify staff users can read user info."""

        self.client.force_authenticate(user=self.staff_user)
        self.assert_http_responses(
            self.endpoint,
            get=status.HTTP_200_OK,
            head=status.HTTP_200_OK,
            options=status.HTTP_200_OK,
            post=status.HTTP_201_CREATED,
            put=status.HTTP_405_METHOD_NOT_ALLOWED,
            patch=status.HTTP_405_METHOD_NOT_ALLOWED,
            delete=status.HTTP_405_METHOD_NOT_ALLOWED,
            trace=status.HTTP_405_METHOD_NOT_ALLOWED,
            post_body={
                'username': 'foobar',
                'password': 'foobar123',
                'first_name': 'Foo',
                'last_name': 'Bar',
                'email': 'foo@bar.com'}
        )


class CredentialHandling(APITestCase):
    """Test the handling of user credentials."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.generic_user = UserFactory(is_staff=False)
        self.staff_user = UserFactory(is_staff=True)

    def test_new_user_credentials_are_set(self) -> None:
        """Verify new users are created with the correctly hashed password.

        Passwords are provided in plain text but stored in the DB as a hash.
        """

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            path='/users/users/',
            data={
                'username': 'foobar',
                'password': 'foobar123',
                'first_name': 'Foo',
                'last_name': 'Bar',
                'email': 'foo@bar.com'
            }
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        # Check the password is stored in the database, but not in plain text
        new_user = User.objects.get(username='foobar')
        self.assertTrue(new_user.check_password('foobar123'))
        self.assertNotEqual(new_user.password, 'foobar123')

        # Verify additional fields
        self.assertEqual(new_user.email, 'foo@bar.com')
        self.assertEqual(new_user.first_name, 'Foo')
        self.assertEqual(new_user.last_name, 'Bar')

    def test_credentials_not_gettable(self) -> None:
        """Verify credentials are not included in get requests."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/users/users/')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.json())

        for record in response.json():
            self.assertNotIn('password', record.keys(), f'Password field found in record: {record}')

    def test_passwords_are_validated(self) -> None:
        """Verify passwords are validated against security requirements."""

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            path='/users/users/',
            data={
                'username': 'foobar',
                'password': 'short',
                'first_name': 'Foo',
                'last_name': 'Bar',
                'email': 'foo@bar.com'
            }
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('This password is too short.', response.content.decode())
