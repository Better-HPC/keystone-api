"""Unit tests for the `parse_ldap_entry` function."""

from apps.users.tasks import parse_ldap_entry
from django.test import TestCase


class ParseLdapEntryMethod(TestCase):
    """Tests for the `parse_ldap_entry` function."""

    def test_returns_none_for_none_dn(self) -> None:
        """Verify `None` is returned when the DN is `None`."""

        result = parse_ldap_entry(None, {"uid": [b"user1"]}, {"username": "uid"})
        self.assertIsNone(result)

    def test_returns_none_for_empty_dn(self) -> None:
        """Verify `None` is returned when the DN is an empty string."""

        result = parse_ldap_entry("", {"uid": [b"user1"]}, {"username": "uid"})
        self.assertIsNone(result)

    def test_returns_none_for_missing_username_attr(self) -> None:
        """Verify `None` is returned when the username attribute is absent from attrs."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"cn": [b"Some User"]},
            {"username": "uid"},
        )

        self.assertIsNone(result)

    def test_returns_none_for_empty_username_attr(self) -> None:
        """Verify `None` is returned when the username attribute is an empty list."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": []},
            {"username": "uid"},
        )

        self.assertIsNone(result)

    def test_parses_bytes_username(self) -> None:
        """Verify a bytes username value is decoded to a string."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1"]},
            {"username": "uid"},
        )

        self.assertEqual(result["username"], "user1")

    def test_parses_string_username(self) -> None:
        """Verify a string username value is passed through unchanged."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": ["user1"]},
            {"username": "uid"},
        )

        self.assertEqual(result["username"], "user1")

    def test_defaults_username_attr_to_uid(self) -> None:
        """Verify `uid` is used as the default username attribute when not specified in attr_map."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1"]},
            {},
        )

        self.assertEqual(result["username"], "user1")

    def test_sets_is_ldap_user_true(self) -> None:
        """Verify `is_ldap_user` is always `True` in the returned dict."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1"]},
            {},
        )

        self.assertTrue(result["is_ldap_user"])

    def test_sets_is_active_true(self) -> None:
        """Verify `is_active` is always `True` in the returned dict."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1"]},
            {},
        )

        self.assertTrue(result["is_active"])

    def test_maps_bytes_attributes(self) -> None:
        """Verify LDAP byte attributes are decoded and mapped to the correct Django fields."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {
                "uid": [b"user1"],
                "givenName": [b"Christopher"],
                "sn": [b"Eccleston"],
                "mail": [b"user1@example.org"],
            },
            {
                "username": "uid",
                "first_name": "givenName",
                "last_name": "sn",
                "email": "mail",
            },
        )

        self.assertEqual(result["first_name"], "Christopher")
        self.assertEqual(result["last_name"], "Eccleston")
        self.assertEqual(result["email"], "user1@example.org")

    def test_maps_string_attributes(self) -> None:
        """Verify LDAP string attributes are mapped to the correct Django fields."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": ["user1"], "givenName": ["Jane"], "sn": ["Smith"]},
            {"username": "uid", "first_name": "givenName", "last_name": "sn"},
        )

        self.assertEqual(result["first_name"], "Jane")
        self.assertEqual(result["last_name"], "Smith")

    def test_skips_missing_optional_attributes(self) -> None:
        """Verify attributes absent from the LDAP entry are not included in the result."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1"]},
            {"username": "uid", "first_name": "givenName", "email": "mail"},
        )

        self.assertNotIn("first_name", result, "Missing LDAP attribute should not appear in result")
        self.assertNotIn("email", result, "Missing LDAP attribute should not appear in result")

    def test_uses_first_value_for_multivalued_attributes(self) -> None:
        """Verify only the first value is used when an attribute has multiple values."""

        result = parse_ldap_entry(
            "uid=user1,ou=users,dc=example,dc=com",
            {"uid": [b"user1", b"user1-alias"], "mail": [b"primary@example.com", b"secondary@example.com"]},
            {"username": "uid", "email": "mail"},
        )

        self.assertEqual(result["username"], "user1")
        self.assertEqual(result["email"], "primary@example.com")
