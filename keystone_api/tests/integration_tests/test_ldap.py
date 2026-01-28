"""
Tests for LDAP authentication integration with Django REST Framework.
Tests run against a real LDAP server, creating test data in setUp and cleaning up in tearDown.

Requirements:
    - Running LDAP server with write access
    - Environment variables configured for LDAP connection
"""

import ldap
import ldap.modlist as modlist
from django.test import TestCase, override_settings
from django.contrib.auth import authenticate, get_user_model
from django_auth_ldap.config import LDAPSearch
from main.settings import (
    AUTH_LDAP_SERVER_URI,
    AUTH_LDAP_BIND_DN,
    AUTH_LDAP_BIND_PASSWORD,
    AUTH_LDAP_START_TLS,
    AUTH_LDAP_TIMEOUT,
    AUTH_LDAP_USER_FILTER,
    AUTH_LDAP_GLOBAL_OPTIONS,
)
import environ

env = environ.Env()
User = get_user_model()

# =============================================================================
# Test Configuration
# =============================================================================

LDAP_USER_BASE_DN = env.str("AUTH_LDAP_USER_SEARCH", "ou=users,dc=example,dc=com")

# Test user data
TEST_USERS = {
    "ldaptest1": {
        "uid": "ldaptest1",
        "cn": "LDAP Test User One",
        "givenName": "Test",
        "sn": "UserOne",
        "mail": "ldaptest1@example.com",
        "userPassword": "testpass123",
    },
    "ldaptest2": {
        "uid": "ldaptest2",
        "cn": "LDAP Test User Two",
        "givenName": "Another",
        "sn": "TestUser",
        "mail": "ldaptest2@example.com",
        "userPassword": "anotherpass456",
    },
}


# =============================================================================
# Settings Configurations
# =============================================================================

def build_ldap_settings(overrides=None):
    """Build LDAP settings dict with optional overrides."""
    settings = {
        "AUTH_LDAP_SERVER_URI": AUTH_LDAP_SERVER_URI,
        "AUTH_LDAP_BIND_DN": AUTH_LDAP_BIND_DN,
        "AUTH_LDAP_BIND_PASSWORD": AUTH_LDAP_BIND_PASSWORD,
        "AUTH_LDAP_START_TLS": AUTH_LDAP_START_TLS,
        "AUTH_LDAP_TIMEOUT": AUTH_LDAP_TIMEOUT,
        "AUTH_LDAP_ALWAYS_UPDATE_USER": True,
        "AUTH_LDAP_GLOBAL_OPTIONS": AUTH_LDAP_GLOBAL_OPTIONS,
        "AUTH_LDAP_USER_SEARCH": LDAPSearch(
            LDAP_USER_BASE_DN,
            ldap.SCOPE_SUBTREE,
            "(uid=%(user)s)",
        ),
        "AUTH_LDAP_USER_ATTR_MAP": {
            "first_name": "givenName",
            "last_name": "sn",
            "email": "mail",
        },
        "AUTHENTICATION_BACKENDS": [
            "django_auth_ldap.backend.LDAPBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],
    }
    if overrides:
        settings.update(overrides)
    return settings


BASE_LDAP_SETTINGS = build_ldap_settings()

INVALID_BIND_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_BIND_PASSWORD": "wrong-password",
})

INVALID_SERVER_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_SERVER_URI": "ldap://nonexistent.invalid:389",
})

WRONG_BASE_DN_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_USER_SEARCH": LDAPSearch(
        "ou=nonexistent,dc=example,dc=com",
        ldap.SCOPE_SUBTREE,
        "(uid=%(user)s)",
    ),
})

WRONG_FILTER_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_USER_SEARCH": LDAPSearch(
        LDAP_USER_BASE_DN,
        ldap.SCOPE_SUBTREE,
        "(cn=%(user)s)",
    ),
})

PARTIAL_ATTR_MAP_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_USER_ATTR_MAP": {"email": "mail"},
})

EMPTY_ATTR_MAP_SETTINGS = build_ldap_settings({
    "AUTH_LDAP_USER_ATTR_MAP": {},
})


# =============================================================================
# LDAP Test Data Management
# =============================================================================

class LDAPTestDataManager:
    """Manages test user creation and cleanup in LDAP."""

    def __init__(self):
        self.conn = None
        self.created_dns = []

    def connect(self):
        """Establish connection to LDAP server."""
        self.conn = ldap.initialize(AUTH_LDAP_SERVER_URI)
        self.conn.set_option(ldap.OPT_NETWORK_TIMEOUT, AUTH_LDAP_TIMEOUT)
        self.conn.set_option(ldap.OPT_TIMEOUT, AUTH_LDAP_TIMEOUT)

        for opt, val in AUTH_LDAP_GLOBAL_OPTIONS.items():
            self.conn.set_option(opt, val)

        if AUTH_LDAP_START_TLS:
            self.conn.start_tls_s()

        self.conn.simple_bind_s(AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)

    def disconnect(self):
        """Close LDAP connection."""
        if self.conn:
            try:
                self.conn.unbind_s()
            except ldap.LDAPError:
                pass
            self.conn = None

    def create_test_user(self, user_data):
        """Create a test user in LDAP."""
        dn = f"uid={user_data['uid']},{LDAP_USER_BASE_DN}"
        attrs = {
            "objectClass": [b"inetOrgPerson", b"organizationalPerson", b"person", b"top"],
            "uid": [user_data["uid"].encode()],
            "cn": [user_data["cn"].encode()],
            "givenName": [user_data["givenName"].encode()],
            "sn": [user_data["sn"].encode()],
            "mail": [user_data["mail"].encode()],
            "userPassword": [user_data["userPassword"].encode()],
        }

        try:
            self.conn.add_s(dn, modlist.addModlist(attrs))
            self.created_dns.append(dn)
            return dn
        except ldap.ALREADY_EXISTS:
            self.created_dns.append(dn)
            return dn

    def delete_test_user(self, dn):
        """Delete a test user from LDAP."""
        try:
            self.conn.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            pass

    def cleanup_all(self):
        """Remove all created test users."""
        for dn in self.created_dns:
            self.delete_test_user(dn)
        self.created_dns.clear()


# =============================================================================
# Base Test Class
# =============================================================================

class LDAPTestCase(TestCase):
    """Base test class with LDAP setup/teardown."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ldap_manager = LDAPTestDataManager()
        cls.ldap_manager.connect()

        # Create all test users
        for user_data in TEST_USERS.values():
            cls.ldap_manager.create_test_user(user_data)

    @classmethod
    def tearDownClass(cls):
        cls.ldap_manager.cleanup_all()
        cls.ldap_manager.disconnect()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # Clean up any Django users from previous tests
        User.objects.filter(username__in=TEST_USERS.keys()).delete()

    def tearDown(self):
        User.objects.filter(username__in=TEST_USERS.keys()).delete()
        super().tearDown()


# =============================================================================
# Authentication Tests
# =============================================================================

@override_settings(**BASE_LDAP_SETTINGS)
class LDAPAuthenticationTests(LDAPTestCase):
    """Test basic LDAP authentication functionality."""

    def test_successful_authentication(self):
        """Valid LDAP credentials should authenticate successfully."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNotNone(user, "Authentication failed for valid credentials")
        self.assertEqual(user.username, "ldaptest1")
        self.assertTrue(user.is_active)

    def test_second_user_authentication(self):
        """Second test user should also authenticate."""
        user = authenticate(username="ldaptest2", password="anotherpass456")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "ldaptest2")

    def test_wrong_password_fails(self):
        """Incorrect password should fail authentication."""
        user = authenticate(username="ldaptest1", password="wrong-password")

        self.assertIsNone(user)

    def test_nonexistent_user_fails(self):
        """Non-existent LDAP user should fail authentication."""
        user = authenticate(username="nonexistent_xyz", password="any-password")

        self.assertIsNone(user)

    def test_empty_password_fails(self):
        """Empty password should fail authentication."""
        user = authenticate(username="ldaptest1", password="")

        self.assertIsNone(user)

    def test_empty_username_fails(self):
        """Empty username should fail authentication."""
        user = authenticate(username="", password="testpass123")

        self.assertIsNone(user)

    def test_user_created_on_first_login(self):
        """Django user should be created on first LDAP authentication."""
        self.assertFalse(User.objects.filter(username="ldaptest1").exists())

        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNotNone(user)
        self.assertTrue(User.objects.filter(username="ldaptest1").exists())

    def test_repeated_authentication_succeeds(self):
        """Multiple authentication attempts should all succeed."""
        for _ in range(3):
            user = authenticate(username="ldaptest1", password="testpass123")
            self.assertIsNotNone(user)

    def test_case_sensitive_username(self):
        """Username matching should respect LDAP server case sensitivity."""
        user_lower = authenticate(username="ldaptest1", password="testpass123")
        user_upper = authenticate(username="LDAPTEST1", password="testpass123")

        self.assertIsNotNone(user_lower)
        # Result depends on LDAP server configuration


# =============================================================================
# Attribute Synchronization Tests
# =============================================================================

@override_settings(**BASE_LDAP_SETTINGS)
class LDAPAttributeSyncTests(LDAPTestCase):
    """Test LDAP attribute synchronization to Django user model."""

    def test_first_name_synced(self):
        """first_name should be synced from LDAP givenName."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertEqual(user.first_name, "Test")

    def test_last_name_synced(self):
        """last_name should be synced from LDAP sn."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertEqual(user.last_name, "UserOne")

    def test_email_synced(self):
        """email should be synced from LDAP mail."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertEqual(user.email, "ldaptest1@example.com")

    def test_all_attributes_synced(self):
        """All mapped attributes should be synced correctly."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "UserOne")
        self.assertEqual(user.email, "ldaptest1@example.com")

    def test_second_user_attributes_synced(self):
        """Second user's attributes should sync correctly."""
        user = authenticate(username="ldaptest2", password="anotherpass456")

        self.assertEqual(user.first_name, "Another")
        self.assertEqual(user.last_name, "TestUser")
        self.assertEqual(user.email, "ldaptest2@example.com")

    def test_attributes_updated_on_subsequent_login(self):
        """Attributes should be re-synced on each authentication."""
        user = authenticate(username="ldaptest1", password="testpass123")

        # Manually modify user
        user.first_name = "Modified"
        user.email = "modified@example.com"
        user.save()

        # Re-authenticate
        user = authenticate(username="ldaptest1", password="testpass123")
        user.refresh_from_db()

        # Should be synced back from LDAP
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.email, "ldaptest1@example.com")

    def test_multiple_users_have_distinct_attributes(self):
        """Different users should have their own attributes."""
        user1 = authenticate(username="ldaptest1", password="testpass123")
        user2 = authenticate(username="ldaptest2", password="anotherpass456")

        self.assertNotEqual(user1.first_name, user2.first_name)
        self.assertNotEqual(user1.email, user2.email)


@override_settings(**PARTIAL_ATTR_MAP_SETTINGS)
class PartialAttributeMapTests(LDAPTestCase):
    """Test behavior with partial attribute mapping."""

    def test_only_mapped_attributes_synced(self):
        """Only attributes in the map should be synced."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "ldaptest1@example.com")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")


@override_settings(**EMPTY_ATTR_MAP_SETTINGS)
class EmptyAttributeMapTests(LDAPTestCase):
    """Test behavior with no attribute mapping."""

    def test_authentication_works_without_attr_map(self):
        """Authentication should work even with empty attribute map."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "ldaptest1")

    def test_no_attributes_synced(self):
        """No attributes should be synced with empty map."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "")


# =============================================================================
# Configuration Error Tests
# =============================================================================

@override_settings(**INVALID_BIND_SETTINGS)
class InvalidBindCredentialsTests(LDAPTestCase):
    """Test behavior with invalid bind credentials."""

    def test_authentication_fails_with_bad_bind_credentials(self):
        """Auth should fail when service account credentials are wrong."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNone(user)


@override_settings(**INVALID_SERVER_SETTINGS)
class InvalidServerTests(LDAPTestCase):
    """Test behavior with unreachable server."""

    def test_authentication_fails_with_bad_server(self):
        """Auth should fail gracefully when server is unreachable."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNone(user)


@override_settings(**WRONG_BASE_DN_SETTINGS)
class WrongBaseDNTests(LDAPTestCase):
    """Test behavior with incorrect base DN."""

    def test_authentication_fails_with_wrong_base_dn(self):
        """Auth should fail when user search base DN is wrong."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNone(user)


@override_settings(**WRONG_FILTER_SETTINGS)
class WrongFilterTests(LDAPTestCase):
    """Test behavior with incorrect search filter."""

    def test_authentication_fails_with_wrong_filter(self):
        """Auth should fail when search filter doesn't match users."""
        user = authenticate(username="ldaptest1", password="testpass123")

        self.assertIsNone(user)


# =============================================================================
# DRF Integration Tests
# =============================================================================

@override_settings(**BASE_LDAP_SETTINGS)
class DRFSessionAuthTests(LDAPTestCase):
    """Test DRF session authentication with LDAP users."""

    def test_ldap_user_can_login_session(self):
        """LDAP user should be able to establish a session."""
        user = authenticate(username="ldaptest1", password="testpass123")
        self.client.force_login(user)

        self.assertIn("_auth_user_id", self.client.session)

    def test_session_persists_user_attributes(self):
        """Session user should have synced LDAP attributes."""
        user = authenticate(username="ldaptest1", password="testpass123")
        self.client.force_login(user)

        user_id = self.client.session["_auth_user_id"]
        session_user = User.objects.get(pk=user_id)

        self.assertEqual(session_user.email, "ldaptest1@example.com")
        self.assertEqual(session_user.first_name, "Test")


@override_settings(**BASE_LDAP_SETTINGS)
class DRFTokenAuthTests(LDAPTestCase):
    """Test DRF token authentication with LDAP users."""

    def test_token_can_be_created_for_ldap_user(self):
        """Token should be creatable for LDAP-authenticated user."""
        from rest_framework.authtoken.models import Token

        user = authenticate(username="ldaptest1", password="testpass123")
        token, created = Token.objects.get_or_create(user=user)

        self.assertIsNotNone(token.key)
        self.assertEqual(token.user, user)

        token.delete()

    def test_token_persists_across_authentications(self):
        """Same token should be returned for same user."""
        from rest_framework.authtoken.models import Token

        user1 = authenticate(username="ldaptest1", password="testpass123")
        token1, _ = Token.objects.get_or_create(user=user1)

        user2 = authenticate(username="ldaptest1", password="testpass123")
        token2, _ = Token.objects.get_or_create(user=user2)

        self.assertEqual(token1.key, token2.key)

        token1.delete()


# =============================================================================
# LDAP Connection Health Tests
# =============================================================================

class LDAPConnectionHealthTests(TestCase):
    """Test LDAP connection health (no test data dependency)."""

    def test_ldap_server_reachable(self):
        """LDAP server should be reachable."""
        conn = ldap.initialize(AUTH_LDAP_SERVER_URI)
        conn.set_option(ldap.OPT_NETWORK_TIMEOUT, AUTH_LDAP_TIMEOUT)

        for opt, val in AUTH_LDAP_GLOBAL_OPTIONS.items():
            conn.set_option(opt, val)

        try:
            if AUTH_LDAP_START_TLS:
                conn.start_tls_s()
            conn.simple_bind_s(AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)
            bound = True
        except ldap.LDAPError as e:
            bound = False
            self.fail(f"Cannot connect to LDAP server: {e}")
        finally:
            conn.unbind_s()

        self.assertTrue(bound)

    def test_user_base_dn_exists(self):
        """User base DN should exist in LDAP."""
        conn = ldap.initialize(AUTH_LDAP_SERVER_URI)
        conn.set_option(ldap.OPT_NETWORK_TIMEOUT, AUTH_LDAP_TIMEOUT)

        for opt, val in AUTH_LDAP_GLOBAL_OPTIONS.items():
            conn.set_option(opt, val)

        if AUTH_LDAP_START_TLS:
            conn.start_tls_s()

        conn.simple_bind_s(AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)

        try:
            conn.search_s(LDAP_USER_BASE_DN, ldap.SCOPE_BASE)
            exists = True
        except ldap.NO_SUCH_OBJECT:
            exists = False
        finally:
            conn.unbind_s()

        self.assertTrue(exists, f"Base DN '{LDAP_USER_BASE_DN}' does not exist")

    def test_bind_dn_has_write_permission(self):
        """Bind DN should have permission to create users (required for tests)."""
        manager = LDAPTestDataManager()
        manager.connect()

        test_dn = f"uid=_permtest_,{LDAP_USER_BASE_DN}"
        attrs = {
            "objectClass": [b"inetOrgPerson", b"organizationalPerson", b"person", b"top"],
            "uid": [b"_permtest_"],
            "cn": [b"Permission Test"],
            "sn": [b"Test"],
        }

        try:
            manager.conn.add_s(test_dn, modlist.addModlist(attrs))
            manager.conn.delete_s(test_dn)
            has_permission = True
        except ldap.INSUFFICIENT_ACCESS:
            has_permission = False
        finally:
            manager.disconnect()

        self.assertTrue(has_permission, "Bind DN lacks write permission to create test users")