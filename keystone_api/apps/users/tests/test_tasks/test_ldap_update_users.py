"""Unit tests for the `ldap_update_users` function."""

from unittest.mock import MagicMock, Mock, patch

from django.test import override_settings, TestCase

from apps.users.factories import UserFactory
from apps.users.models import User
from apps.users.tasks import ldap_update_users


class LdapUpdateUsersMethod(TestCase):
    """Test the updating of user data via the `ldap_update_users` method."""

    @override_settings(AUTH_LDAP_SERVER_URI=None)
    def test_exit_silently_when_uri_is_none(self) -> None:
        """Verify the function exits gracefully when no LDAP server URI is provided."""

        ldap_update_users()

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_USER_SEARCH=MagicMock(base_dn='dc=example,dc=com'),
        AUTH_LDAP_USER_ATTR_MAP={'username': 'uid'},
    )
    @patch('apps.users.tasks.get_ldap_connection')
    @patch('apps.users.tasks.LDAPBackend')
    def test_users_are_created(self, ldap_backend: Mock, mock_get_ldap_connection: Mock) -> None:
        """Verify users are updated from LDAP data."""

        # Mock LDAP search results
        mock_conn = mock_get_ldap_connection.return_value
        mock_conn.search_s.return_value = [
            ('uid=user1,ou=users,dc=example,dc=com', {'uid': [b'user1']}),
            ('uid=user2,ou=users,dc=example,dc=com', {'uid': [b'user2']}),
        ]

        # Mock backend to return user objects
        mock_backend = ldap_backend.return_value
        mock_backend.populate_user.side_effect = lambda username: User(username=username)

        # Test users are created
        ldap_update_users()
        user1 = User.objects.get(username='user1')
        user2 = User.objects.get(username='user2')

        # Verify that the users have the is_ldap_user flag set
        self.assertTrue(user1.is_ldap_user)
        self.assertTrue(user2.is_ldap_user)

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_USER_SEARCH=MagicMock(base_dn='dc=example,dc=com'),
        AUTH_LDAP_USER_ATTR_MAP={'username': 'uid'},
    )
    @patch('apps.users.tasks.get_ldap_connection')
    def test_no_users_account_found(self, mock_get_ldap_connection: Mock) -> None:
        """Verify the function exits silently when no user accounts are found in LDAP."""

        mock_conn = mock_get_ldap_connection.return_value
        mock_conn.search_s.return_value = []
        ldap_update_users()

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_USER_SEARCH=MagicMock(base_dn='dc=example,dc=com'),
        AUTH_LDAP_USER_ATTR_MAP={'username': 'uid'},
        AUTH_LDAP_PURGE_REMOVED=True,
    )
    @patch('apps.users.tasks.get_ldap_connection')
    def test_users_are_pruned(self, mock_get_ldap_connection: Mock) -> None:
        """Verify missing user accounts are deleted when `AUTH_LDAP_PURGE_REMOVED=True`."""

        # Mock an LDAP search result with no users
        mock_conn = MagicMock()
        mock_conn.search_s.return_value = []
        mock_get_ldap_connection.return_value = mock_conn

        # Create users
        UserFactory(username='user_to_prune', is_ldap_user=True)
        UserFactory(username='non_ldap_user', is_ldap_user=False)

        # Test missing LDAP users are deleted and non-ldap users are not modified
        ldap_update_users()
        self.assertFalse(User.objects.filter(username='user_to_prune').exists())
        self.assertTrue(User.objects.filter(username='non_ldap_user').exists())

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_USER_SEARCH=MagicMock(base_dn='dc=example,dc=com'),
        AUTH_LDAP_USER_ATTR_MAP={'username': 'uid'},
        AUTH_LDAP_PURGE_REMOVED=False
    )
    @patch('apps.users.tasks.get_ldap_connection')
    def test_users_are_deactivated(self, mock_get_ldap_connection: Mock) -> None:
        """Verify missing LDAP users are deactivated when `AUTH_LDAP_PURGE_REMOVED=False`."""

        # Mock an LDAP search result with no users
        mock_conn = MagicMock()
        mock_conn.search_s.return_value = []
        mock_get_ldap_connection.return_value = mock_conn

        # Create users
        UserFactory(username='user_to_deactivate', is_ldap_user=True, is_active=True)
        UserFactory(username='non_ldap_user', is_ldap_user=False, is_active=True)

        # Test missing LDAP users are deactivated and non-ldap users are not modified
        ldap_update_users()
        self.assertFalse(User.objects.get(username='user_to_deactivate').is_active)
        self.assertTrue(User.objects.get(username='non_ldap_user').is_active)
