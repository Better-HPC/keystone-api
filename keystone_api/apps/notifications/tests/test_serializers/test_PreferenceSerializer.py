"""Unit tests for the `PreferenceSerializer` class."""

from django.test import TestCase


class ValidateUserMethod(TestCase):
    """Test validation of the `user` field."""

    def setUp(self) -> None:
        """Create dummy user accounts and test data."""

    def test_field_matches_submitter(self) -> None:
        """Verify validation passes when the user field equals the user submitting the HTTP request."""

        self.fail()

    def test_different_field_from_submitter(self) -> None:
        """Verify validation fails when the user field is different from the user submitting the HTTP request."""

        self.fail()

    def test_staff_override_validation(self) -> None:
        """Verify staff users bypass validation."""

        self.fail()

    def test_field_is_optional(self) -> None:
        """Verify the user field is optional."""

        self.fail()
