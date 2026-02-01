"""Unit tests for the `ldap_dependency_check` function."""

from unittest import mock
from unittest.mock import Mock

from django.test import override_settings, SimpleTestCase

from apps.users.checks import ldap_dependency_check


class LdapDependencyCheckMethod(SimpleTestCase):
    """Test the verification of LDAP dependencies via the `ldap_dependency_check` method."""

    @override_settings(AUTH_LDAP_SERVER_URI="ldap://example.com")
    @mock.patch("builtins.__import__")
    def test_ldap_check_no_errors_when_ldap_installed(self, mock_import: Mock) -> None:
        """Verify no errors are returned when LDAP is installed and required."""

        mock_import.side_effect = None
        self.assertEqual([], ldap_dependency_check())

    @override_settings(AUTH_LDAP_SERVER_URI="ldap://example.com")
    @mock.patch("builtins.__import__")
    def test_ldap_check_error_when_ldap_not_installed(self, mock_import: Mock) -> None:
        """Verify an error is returned when LDAP is required but not installed."""

        mock_import.side_effect = ImportError
        errors = ldap_dependency_check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "users.E001")

    @override_settings(AUTH_LDAP_SERVER_URI="")
    @mock.patch("builtins.__import__")
    def test_ldap_check_no_errors_when_ldap_not_required(self, mock_import: Mock) -> None:
        """Verify no errors are returned when LDAP is not required."""

        mock_import.side_effect = ImportError
        self.assertEqual([], ldap_dependency_check())
