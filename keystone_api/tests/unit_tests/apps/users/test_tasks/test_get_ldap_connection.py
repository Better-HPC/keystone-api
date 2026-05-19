"""Unit tests for the `get_ldap_connection` function."""

from unittest.mock import MagicMock, patch

from apps.users.tasks import get_ldap_connection
from django.test import override_settings, TestCase


class GetLdapConnectionMethod(TestCase):
    """Test connecting to LDAP via the `get_ldap_connection` method."""

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=False,
    )
    @patch("apps.users.tasks.ldap")
    def test_initializes_connection(self, mock_ldap: MagicMock) -> None:
        """Verify the connection is initialized with the configured server URI."""

        get_ldap_connection()
        mock_ldap.initialize.assert_called_once_with("ldap://ds.example.com:389")

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="cn=admin,dc=example,dc=com",
        AUTH_LDAP_BIND_PASSWORD="secret",
        AUTH_LDAP_START_TLS=False,
    )
    @patch("apps.users.tasks.ldap")
    def test_binds_when_dn_provided(self, mock_ldap: MagicMock) -> None:
        """Verify the connection binds with credentials when a bind DN is configured."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.bind.assert_called_once_with("cn=admin,dc=example,dc=com", "secret")

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=False,
    )
    @patch("apps.users.tasks.ldap")
    def test_skips_bind_when_no_dn(self, mock_ldap: MagicMock) -> None:
        """Verify the connection does not bind when no bind DN is configured."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.bind.assert_not_called()

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=True,
    )
    @patch("apps.users.tasks.ldap")
    def test_starts_tls_when_enabled(self, mock_ldap: MagicMock) -> None:
        """Verify TLS is started and the cert option is set when `AUTH_LDAP_START_TLS` is `True`."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_ldap.set_option.assert_called_once_with(
            mock_ldap.OPT_X_TLS_REQUIRE_CERT,
            mock_ldap.OPT_X_TLS_NEVER,
        )
        mock_conn.start_tls_s.assert_called_once()

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=False,
    )
    @patch("apps.users.tasks.ldap")
    def test_skips_tls_when_disabled(self, mock_ldap: MagicMock) -> None:
        """Verify TLS is not started when `AUTH_LDAP_START_TLS` is `False`."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.start_tls_s.assert_not_called()

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=False,
        AUTH_LDAP_TIMEOUT=30,
    )
    @patch("apps.users.tasks.ldap")
    def test_sets_timeout_options(self, mock_ldap: MagicMock) -> None:
        """Verify both timeout options are set on the connection."""

        mock_conn = mock_ldap.initialize.return_value
        get_ldap_connection()
        mock_conn.set_option.assert_any_call(mock_ldap.OPT_TIMEOUT, 30)
        mock_conn.set_option.assert_any_call(mock_ldap.OPT_NETWORK_TIMEOUT, 30)

    @override_settings(
        AUTH_LDAP_SERVER_URI="ldap://ds.example.com:389",
        AUTH_LDAP_BIND_DN="",
        AUTH_LDAP_START_TLS=False,
    )
    @patch("apps.users.tasks.ldap")
    def test_returns_connection_object(self, mock_ldap: MagicMock) -> None:
        """Verify the initialized connection object is returned."""

        mock_conn = mock_ldap.initialize.return_value
        result = get_ldap_connection()
        self.assertEqual(result, mock_conn)
