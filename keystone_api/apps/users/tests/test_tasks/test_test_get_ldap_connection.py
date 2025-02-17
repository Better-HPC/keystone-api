"""Unit tests for the `test_get_ldap_connection` function."""

from unittest.mock import Mock, patch

import ldap
from django.test import override_settings, TestCase

from apps.users.tasks import get_ldap_connection


class GetLdapConnectionMethod(TestCase):
    """Test connecting to LDAP via the `get_ldap_connection` method."""

    @override_settings(
        AUTH_LDAP_SERVER_URI='ldap://testserver',
        AUTH_LDAP_BIND_DN='cn=admin,dc=example,dc=com',
        AUTH_LDAP_BIND_PASSWORD='password123',
        AUTH_LDAP_START_TLS=True
    )
    @patch('ldap.initialize')
    @patch('ldap.set_option')
    @patch('ldap.ldapobject.LDAPObject')
    def test_tls_configuration(self, mock_ldap: Mock, mock_set_option: Mock, mock_initialize: Mock) -> None:
        """Verify the returned LDAP connection is configured with TLS enabled."""

        # Set up mock objects
        mock_conn = mock_ldap.return_value
        mock_initialize.return_value = mock_conn
        mock_set_option.return_value = None

        # Call the function to test
        conn = get_ldap_connection()
        self.assertEqual(conn, mock_conn)

        # Check the connection calls
        mock_initialize.assert_called_once_with('ldap://testserver')
        mock_conn.bind.assert_called_once_with('cn=admin,dc=example,dc=com', 'password123')
        mock_set_option.assert_called_once_with(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
