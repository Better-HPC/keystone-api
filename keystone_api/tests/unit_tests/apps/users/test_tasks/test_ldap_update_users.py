"""Unit tests for the `ldap_update_users` function."""

from unittest.mock import MagicMock, Mock, patch

from apps.users.factories import UserFactory
from apps.users.models import User
from apps.users.tasks import ldap_update_users
from django.test import override_settings, TestCase

LDAP_BASE_SETTINGS = {
    "AUTH_LDAP_SERVER_URI": "ldap://ds.example.com:389",
    "AUTH_LDAP_BIND_DN": "",
    "AUTH_LDAP_BIND_PASSWORD": "",
    "AUTH_LDAP_START_TLS": False,
    "AUTH_LDAP_TIMEOUT": 30,
    "AUTH_LDAP_USER_SEARCH": MagicMock(base_dn="dc=example,dc=com"),
    "AUTH_LDAP_USER_FILTER": "(objectClass=person)",
    "AUTH_LDAP_USER_ATTR_MAP": {"username": "uid"},
}


class LdapUpdateUsersMethod(TestCase):
    """Tests for the `ldap_update_users` task."""

    @override_settings(AUTH_LDAP_SERVER_URI=None)
    def test_exits_silently_when_uri_not_configured(self) -> None:
        """Verify the function returns without error when no LDAP URI is configured."""

        ldap_update_users()

    @override_settings(**LDAP_BASE_SETTINGS)
    @patch("apps.users.tasks.get_ldap_connection")
    def test_creates_new_users(self, mock_get_ldap_connection: Mock) -> None:
        """Verify new user accounts are created from LDAP entries."""

        mock_get_ldap_connection.return_value.search_s.return_value = [
            ("uid=user1,ou=users,dc=example,dc=com", {"uid": [b"user1"]}),
            ("uid=user2,ou=users,dc=example,dc=com", {"uid": [b"user2"]}),
        ]

        ldap_update_users()

        self.assertTrue(User.objects.get(username="user1").is_ldap_user)
        self.assertTrue(User.objects.get(username="user2").is_ldap_user)

    @override_settings(**{
        **LDAP_BASE_SETTINGS,
        "AUTH_LDAP_USER_ATTR_MAP": {
            "username": "uid",
            "first_name": "givenName",
            "last_name": "sn",
            "email": "mail",
        },
    })
    @patch("apps.users.tasks.get_ldap_connection")
    def test_updates_existing_users(self, mock_get_ldap_connection: Mock) -> None:
        """Verify existing user accounts are updated with current LDAP data."""

        UserFactory(username="user1", first_name="Old", last_name="Name", is_ldap_user=True)
        mock_get_ldap_connection.return_value.search_s.return_value = [
            (
                "uid=user1,ou=users,dc=example,dc=com",
                {
                    "uid": [b"user1"],
                    "givenName": [b"New"],
                    "sn": [b"Name"],
                    "mail": [b"user1@example.com"],
                },
            ),
        ]

        ldap_update_users()

        user = User.objects.get(username="user1")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.email, "user1@example.com")

    @override_settings(**{
        **LDAP_BASE_SETTINGS,
        "AUTH_LDAP_USER_ATTR_MAP": {
            "username": "uid",
            "first_name": "givenName",
        },
    })
    @patch("apps.users.tasks.get_ldap_connection")
    def test_preserves_fields_absent_from_ldap(self, mock_get_ldap_connection: Mock) -> None:
        """Verify fields not present in the LDAP response are not overwritten on existing records."""

        UserFactory(username="user1", email="preserved@example.com", is_ldap_user=True)
        mock_get_ldap_connection.return_value.search_s.return_value = [
            ("uid=user1,ou=users,dc=example,dc=com", {"uid": [b"user1"], "givenName": [b"Chris"]}),
        ]

        ldap_update_users()

        self.assertEqual(
            User.objects.get(username="user1").email,
            "preserved@example.com",
            "Email should not be overwritten when absent from LDAP response",
        )

    @override_settings(**LDAP_BASE_SETTINGS)
    @patch("apps.users.tasks.get_ldap_connection")
    def test_deactivates_users_removed_from_ldap(self, mock_get_ldap_connection: Mock) -> None:
        """Verify LDAP users no longer present in the directory are deactivated."""

        UserFactory(username="removed_user", is_ldap_user=True, is_active=True)
        mock_get_ldap_connection.return_value.search_s.return_value = []

        ldap_update_users()

        self.assertFalse(
            User.objects.get(username="removed_user").is_active,
            "User absent from LDAP should be deactivated",
        )

    @override_settings(**LDAP_BASE_SETTINGS)
    @patch("apps.users.tasks.get_ldap_connection")
    def test_non_ldap_users_are_not_deactivated(self, mock_get_ldap_connection: Mock) -> None:
        """Verify non-LDAP users are not deactivated when absent from the LDAP directory."""

        UserFactory(username="local_user", is_ldap_user=False, is_active=True)
        mock_get_ldap_connection.return_value.search_s.return_value = []

        ldap_update_users()

        self.assertTrue(
            User.objects.get(username="local_user").is_active,
            "Non-LDAP user should not be affected by LDAP sync",
        )

    @override_settings(**LDAP_BASE_SETTINGS)
    @patch("apps.users.tasks.get_ldap_connection")
    def test_handles_empty_ldap_results(self, mock_get_ldap_connection: Mock) -> None:
        """Verify the function exits without error when LDAP returns no entries."""

        mock_get_ldap_connection.return_value.search_s.return_value = []
        ldap_update_users()

    @override_settings(**LDAP_BASE_SETTINGS)
    @patch("apps.users.tasks.get_ldap_connection")
    def test_skips_referral_entries(self, mock_get_ldap_connection: Mock) -> None:
        """Verify referral entries in LDAP results are skipped without error."""

        mock_get_ldap_connection.return_value.search_s.return_value = [
            (None, ["ldap://other-server/dc=example,dc=com"]),
            ("uid=user1,ou=users,dc=example,dc=com", {"uid": [b"user1"]}),
        ]

        ldap_update_users()

        self.assertEqual(User.objects.count(), 1, "Only the non-referral entry should be created")
        self.assertTrue(User.objects.filter(username="user1").exists())
