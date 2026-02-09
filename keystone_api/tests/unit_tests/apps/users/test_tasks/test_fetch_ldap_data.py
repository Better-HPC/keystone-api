"""Unit tests for the `fetch_ldap_data` function."""

from unittest.mock import call, Mock, patch

import ldap
from django.test import override_settings, TestCase

from apps.users.tasks import fetch_ldap_data


@override_settings(
    AUTH_LDAP_SERVER_URI='ldap://test.example.com',
    AUTH_LDAP_USER_SEARCH=Mock(base_dn='dc=example,dc=com'),
    AUTH_LDAP_USER_FILTER='(objectClass=person)',
    AUTH_LDAP_BIND_DN='cn=admin,dc=example,dc=com',
    AUTH_LDAP_BIND_PASSWORD='password',
    AUTH_LDAP_START_TLS=False,
    AUTH_LDAP_TIMEOUT=10,
)
class FetchLdapDataMethod(TestCase):
    """Test the fetching of user data from LDAP with retry logic."""

    @patch('apps.users.tasks.get_ldap_connection')
    def test_first_attempt_successful(self, mock_get_conn: Mock) -> None:
        """Verify LDAP data is returned when fetched successfully on the first attempt."""

        mock_conn = Mock()
        mock_search_results = [
            ('cn=user1,dc=example,dc=com', {'uid': [b'user1'], 'mail': [b'user1@example.com']}),
            ('cn=user2,dc=example,dc=com', {'uid': [b'user2'], 'mail': [b'user2@example.com']}),
        ]

        mock_conn.search_s.return_value = mock_search_results
        mock_get_conn.return_value = mock_conn

        result = fetch_ldap_data(attempts=3, delay=1.0)

        self.assertEqual(result, mock_search_results)
        mock_get_conn.assert_called_once()
        mock_conn.search_s.assert_called_once_with(
            'dc=example,dc=com',
            ldap.SCOPE_SUBTREE,
            '(objectClass=person)'
        )

    @patch('apps.users.tasks.time.sleep')
    @patch('apps.users.tasks.get_ldap_connection')
    def test_connection_failure_retry(self, mock_get_conn: Mock, mock_sleep: Mock) -> None:
        """Verify LDAP data is fetched successfully after two connection failures."""

        mock_conn = Mock()
        mock_search_results = [
            ('cn=user1,dc=example,dc=com', {'uid': [b'user1']}),
        ]

        mock_get_conn.side_effect = [
            Exception('Connection timeout'),
            Exception('Server unavailable'),
            mock_conn,
        ]

        mock_conn.search_s.return_value = mock_search_results
        result = fetch_ldap_data(attempts=3, delay=1.0)

        self.assertEqual(result, mock_search_results)
        self.assertEqual(mock_get_conn.call_count, 3)

    @patch('apps.users.tasks.time.sleep')
    @patch('apps.users.tasks.get_ldap_connection')
    def test_search_failure_retry(self, mock_get_conn: Mock, mock_sleep: Mock) -> None:
        """Verify LDAP data is fetched successfully after two search failures."""

        mock_conn_1 = Mock()
        mock_conn_1.search_s.side_effect = Exception('Search failed')

        mock_conn_2 = Mock()
        mock_conn_2.search_s.side_effect = Exception('Search timeout')

        mock_conn_3 = Mock()
        mock_search_results = [('cn=user1,dc=example,dc=com', {'uid': [b'user1']})]
        mock_conn_3.search_s.return_value = mock_search_results

        mock_get_conn.side_effect = [mock_conn_1, mock_conn_2, mock_conn_3]

        result = fetch_ldap_data(attempts=3, delay=1.0)

        self.assertEqual(result, mock_search_results)
        self.assertEqual(mock_get_conn.call_count, 3)

    @patch('apps.users.tasks.time.sleep')
    @patch('apps.users.tasks.get_ldap_connection')
    def test_all_attempts_exhausted(self, mock_get_conn: Mock, mock_sleep: Mock) -> None:
        """Verify an exception is raised when all attempts are exhausted."""

        mock_get_conn.side_effect = Exception('Connection timeout')

        with self.assertRaises(Exception) as context:
            fetch_ldap_data(attempts=3, delay=1.0)

        self.assertEqual(str(context.exception), 'Connection timeout')
        self.assertEqual(mock_get_conn.call_count, 3)

    @patch('apps.users.tasks.get_ldap_connection')
    def test_single_attempt(self, mock_get_conn: Mock) -> None:
        """Verify only one connection attempt is made when `attempts` is set to 1."""

        mock_get_conn.side_effect = Exception('Connection failed')

        with self.assertRaises(Exception):
            fetch_ldap_data(attempts=1, delay=1.0)

        self.assertEqual(mock_get_conn.call_count, 1)

    @patch('apps.users.tasks.time.sleep')
    @patch('apps.users.tasks.get_ldap_connection')
    def test_exponential_backoff_timing(self, mock_get_conn: Mock, mock_sleep: Mock) -> None:
        """Verify exponential backoff calculates correct wait times between retries."""

        mock_get_conn.side_effect = Exception('Connection timeout')

        with self.assertRaises(Exception):
            fetch_ldap_data(attempts=4, delay=2.0)

        expected_sleep_calls = [call(2.0), call(4.0), call(8.0)]
        mock_sleep.assert_has_calls(expected_sleep_calls)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('apps.users.tasks.time.sleep')
    @patch('apps.users.tasks.get_ldap_connection')
    def test_custom_delay_parameter(self, mock_get_conn: Mock, mock_sleep: Mock) -> None:
        """Verify custom delay parameter values are respected in exponential backoff calculations."""

        mock_get_conn.side_effect = Exception('Connection timeout')

        with self.assertRaises(Exception):
            fetch_ldap_data(attempts=4, delay=5.0)

        expected_sleep_calls = [call(5.0), call(10.0), call(20.0)]
        mock_sleep.assert_has_calls(expected_sleep_calls)
        self.assertEqual(mock_sleep.call_count, 3)

    def test_zero_attempts(self) -> None:
        """Verify a zero `attempts` argument raises a `RuntimeError`."""

        with self.assertRaisesRegex(RuntimeError, "`attempts` argument must be greater or equal to 1"):
            fetch_ldap_data(attempts=0)

    def test_negative_attempts(self) -> None:
        """Verify a negative `attempts` argument raises a `RuntimeError`."""

        with self.assertRaisesRegex(RuntimeError, "`attempts` argument must be greater or equal to 1"):
            fetch_ldap_data(attempts=-1)

    def test_negative_delay(self) -> None:
        """Verify a negative `delay` argument raises a `RuntimeError`."""

        with self.assertRaisesRegex(RuntimeError, "`delay` argument must be greater or equal to 0"):
            fetch_ldap_data(delay=-1)
