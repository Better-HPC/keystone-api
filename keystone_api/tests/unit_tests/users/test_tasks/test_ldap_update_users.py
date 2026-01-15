"""Unit tests for the `ldap_update_users` function."""

from unittest.mock import MagicMock, Mock, patch

from django.test import override_settings, TestCase

from apps.users.factories import UserFactory
from apps.users.models import User
from apps.users.tasks import get_ldap_connection, ldap_update_users, parse_ldap_entry


class GetLdapConnectionMethod(TestCase):
    """Test the establishment of LDAP connections via the `get_ldap_connection` function."""

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=False,
    )
    @patch('apps.users.tasks.ldap')
    def test_initializes_connection(self, mock_ldap: MagicMock) -> None:
        """Verify the connection is initialized with the configured URI."""

        get_ldap_connection()
        mock_ldap.initialize.assert_called_once_with('ldap://ds.example.com:389')

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='cn=admin,dc=example,dc=com',
        AUTH_LDAP_BIND_PASSWORD='secret',
        AUTH_LDAP_START_TLS=False,
    )
    @patch('apps.users.tasks.ldap')
    def test_binds_when_dn_provided(self, mock_ldap: MagicMock) -> None:
        """Verify the connection binds with credentials when a bind DN is provided."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.bind.assert_called_once_with('cn=admin,dc=example,dc=com', 'secret')

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=False,
    )
    @patch('apps.users.tasks.ldap')
    def test_skips_bind_when_no_dn(self, mock_ldap: MagicMock) -> None:
        """Verify the connection does not bind when no bind DN is provided."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.bind.assert_not_called()

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=True,
    )
    @patch('apps.users.tasks.ldap')
    def test_starts_tls_when_enabled(self, mock_ldap: MagicMock) -> None:
        """Verify TLS is started when `AUTH_LDAP_START_TLS` is `True`."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_ldap.set_option.assert_called_once_with(
            mock_ldap.OPT_X_TLS_REQUIRE_CERT,
            mock_ldap.OPT_X_TLS_NEVER
        )
        mock_conn.start_tls_s.assert_called_once()

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=False,
    )
    @patch('apps.users.tasks.ldap')
    def test_skips_tls_when_disabled(self, mock_ldap: MagicMock) -> None:
        """Verify TLS is not started when `AUTH_LDAP_START_TLS` is `False`."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.start_tls_s.assert_not_called()

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=False,
    )
    @patch('apps.users.tasks.ldap')
    def test_returns_connection_object(self, mock_ldap: MagicMock) -> None:
        """Verify the function returns the LDAP connection object."""

        mock_conn = mock_ldap.initialize.return_value
        result = get_ldap_connection()
        self.assertEqual(result, mock_conn)

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://ds.example.com:389',
        AUTH_LDAP_BIND_DN='',
        AUTH_LDAP_START_TLS=False,
        AUTH_LDAP_TIMEOUT=30,
    )
    @patch('apps.users.tasks.ldap')
    def test_sets_timeout_options(self, mock_ldap: MagicMock) -> None:
        """Verify timeout options are set on the connection."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()

        mock_conn.set_option.assert_any_call(mock_ldap.OPT_TIMEOUT, 30)
        mock_conn.set_option.assert_any_call(mock_ldap.OPT_NETWORK_TIMEOUT, 30)


class ParseLdapEntryMethod(TestCase):
    """Test the parsing of LDAP entries via the `parse_ldap_entry` function."""

    def test_returns_none_for_referral(self) -> None:
        """Verify referral entries return `None`."""

        result = parse_ldap_entry(None, ['ldap://other-server/dc=example,dc=com'], {})
        self.assertIsNone(result)

    def test_returns_none_for_missing_username(self) -> None:
        """Verify entries without a username attribute return `None`."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'cn': [b'Some User']},
            {'username': 'uid'}
        )

        self.assertIsNone(result)

    def test_parses_username_with_default_attribute(self) -> None:
        """Verify the username is parsed from the uid when not specified in attr_map."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'uid': [b'user1']},
            {}
        )

        self.assertEqual(result['username'], 'user1')

    def test_parses_username_with_custom_attribute(self) -> None:
        """Verify the username is parsed from a custom attribute."""

        result = parse_ldap_entry(
            'cn=jsmith,ou=users,dc=example,dc=com',
            {'sAMAccountName': [b'jsmith']},
            {'username': 'sAMAccountName'}
        )

        self.assertEqual(result['username'], 'jsmith')

    def test_sets_ldap_user_flags(self) -> None:
        """Verify `is_ldap_user` and `is_active` are set correctly."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'uid': [b'user1']},
            {}
        )

        self.assertTrue(result['is_ldap_user'])
        self.assertTrue(result['is_active'])

    def test_maps_attributes(self) -> None:
        """Verify LDAP attributes are mapped to Django user fields."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {
                'uid': [b'user1'],
                'givenName': [b'Christopher'],
                'sn': [b'Eccleston'],
                'mail': [b'user1@example.org'],
            },
            {
                'username': 'uid',
                'first_name': 'givenName',
                'last_name': 'sn',
                'email': 'mail',
            }
        )

        self.assertEqual(result['first_name'], 'Christopher')
        self.assertEqual(result['last_name'], 'Eccleston')
        self.assertEqual(result['email'], 'user1@example.org')

    def test_skips_missing_attributes(self) -> None:
        """Verify missing LDAP attributes are not included in the result."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'uid': [b'user1']},
            {'username': 'uid', 'first_name': 'givenName', 'email': 'mail'}
        )

        self.assertNotIn('first_name', result)
        self.assertNotIn('email', result)

    def test_decodes_bytes(self) -> None:
        """Verify byte values are decoded to strings."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'uid': [b'user1'], 'sn': [b'Eccleston']},
            {'username': 'uid', 'last_name': 'sn'}
        )

        self.assertIsInstance(result['username'], str)
        self.assertIsInstance(result['last_name'], str)

    def test_handles_string_values(self) -> None:
        """Verify string values are passed through unchanged."""

        result = parse_ldap_entry(
            'uid=user1,ou=users,dc=example,dc=com',
            {'uid': ['user1'], 'sn': ['Eccleston']},
            {'username': 'uid', 'last_name': 'sn'}
        )

        self.assertEqual(result['username'], 'user1')
        self.assertEqual(result['last_name'], 'Eccleston')


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
    def test_users_are_created(self, mock_get_ldap_connection: Mock) -> None:
        """Verify users are created from LDAP data."""

        # Mock LDAP search results
        mock_conn = mock_get_ldap_connection.return_value
        mock_conn.search_s.return_value = [
            ('uid=user1,ou=users,dc=example,dc=com', {'uid': [b'user1']}),
            ('uid=user2,ou=users,dc=example,dc=com', {'uid': [b'user2']}),
        ]

        ldap_update_users()

        user1 = User.objects.get(username='user1')
        user2 = User.objects.get(username='user2')

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
