"""Unit tests for the `parse_ldap_entry` function."""

from django.test import TestCase

from apps.users.tasks import parse_ldap_entry


class ParseLdapEntry(TestCase):
    """Test the parsing of LDAP entries into propperly formatted application data."""

    def test_returns_none_when_dn_is_empty(self) -> None:
        """Verify `None` is returned for referral entries with empty DN."""

        result = parse_ldap_entry('', {'uid': [b'testuser']}, {'username': 'uid'})

        self.assertIsNone(result)

    def test_returns_none_when_dn_is_none(self) -> None:
        """Verify `None` is returned when DN is `None`."""

        result = parse_ldap_entry(None, {'uid': [b'testuser']}, {'username': 'uid'})

        self.assertIsNone(result)

    def test_returns_none_when_username_attr_missing(self) -> None:
        """Verify `None` is returned when username attribute is missing."""

        result = parse_ldap_entry('cn=test,dc=example,dc=com', {}, {'username': 'uid'})

        self.assertIsNone(result)

    def test_returns_none_when_username_attr_empty(self) -> None:
        """Verify `None` is returned when username attribute is empty list."""

        result = parse_ldap_entry('cn=test,dc=example,dc=com', {'uid': []}, {'username': 'uid'})

        self.assertIsNone(result)

    def test_decodes_bytes_username(self) -> None:
        """Verify a bytes username value is decoded to string."""

        result = parse_ldap_entry(
            'cn=test,dc=example,dc=com',
            {'uid': [b'testuser']},
            {'username': 'uid'}
        )

        self.assertEqual('testuser', result['username'])

    def test_handles_string_username(self) -> None:
        """Verify a string username is handled correctly."""

        result = parse_ldap_entry(
            'cn=test,dc=example,dc=com',
            {'uid': ['testuser']},
            {'username': 'uid'}
        )

        self.assertEqual('testuser', result['username'])

    def test_sets_is_ldap_user_true(self) -> None:
        """Verify `is_ldap_user` is set to `True` in the returned values."""

        result = parse_ldap_entry(
            'cn=test,dc=example,dc=com',
            {'uid': [b'testuser']},
            {'username': 'uid'}
        )

        self.assertTrue(result['is_ldap_user'])

    def test_sets_is_active_true(self) -> None:
        """Verify is_active is set to `True` in the returned values."""

        result = parse_ldap_entry(
            'cn=test,dc=example,dc=com',
            {'uid': [b'testuser']},
            {'username': 'uid'}
        )

        self.assertTrue(result['is_active'])

    def test_maps_additional_fields_from_bytes(self) -> None:
        """Verify additional fields are mapped and decoded from bytes."""

        attrs = {
            'uid': [b'testuser'],
            'givenName': [b'John'],
            'sn': [b'Doe'],
            'mail': [b'john.doe@example.com'],
        }
        attr_map = {
            'username': 'uid',
            'first_name': 'givenName',
            'last_name': 'sn',
            'email': 'mail',
        }

        result = parse_ldap_entry('cn=test,dc=example,dc=com', attrs, attr_map)

        self.assertEqual('John', result['first_name'])
        self.assertEqual('Doe', result['last_name'])
        self.assertEqual('john.doe@example.com', result['email'])

    def test_maps_additional_fields_from_strings(self) -> None:
        """Verify additional fields are mapped correctly from strings."""

        attrs = {
            'uid': ['testuser'],
            'givenName': ['Jane'],
            'sn': ['Smith'],
        }
        attr_map = {
            'username': 'uid',
            'first_name': 'givenName',
            'last_name': 'sn',
        }

        result = parse_ldap_entry('cn=test,dc=example,dc=com', attrs, attr_map)

        self.assertEqual('Jane', result['first_name'])
        self.assertEqual('Smith', result['last_name'])

    def test_skips_missing_optional_fields(self) -> None:
        """Verify missing optional fields are not included in the result."""

        attrs = {'uid': [b'testuser']}
        attr_map = {
            'username': 'uid',
            'first_name': 'givenName',
            'email': 'mail',
        }

        result = parse_ldap_entry('cn=test,dc=example,dc=com', attrs, attr_map)

        self.assertNotIn('first_name', result)
        self.assertNotIn('email', result)

    def test_uses_default_uid_when_username_not_in_map(self) -> None:
        """Verify `uid` is used as default username attribute."""

        result = parse_ldap_entry(
            'cn=test,dc=example,dc=com',
            {'uid': [b'defaultuser']},
            {}
        )

        self.assertEqual('defaultuser', result['username'])

    def test_uses_first_value_from_multivalued_attribute(self) -> None:
        """Verify only the first value is used for multi-valued attributes."""

        attrs = {
            'uid': [b'user1', b'user2'],
            'mail': [b'first@example.com', b'second@example.com'],
        }
        attr_map = {'username': 'uid', 'email': 'mail'}

        result = parse_ldap_entry('cn=test,dc=example,dc=com', attrs, attr_map)

        self.assertEqual('user1', result['username'])
        self.assertEqual('first@example.com', result['email'])
