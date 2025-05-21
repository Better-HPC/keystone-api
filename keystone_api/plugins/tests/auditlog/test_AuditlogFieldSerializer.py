"""Unit tests for the `AuditlogFieldSerializer` class."""

from unittest import TestCase

from plugins.auditlog import AuditlogFieldSerializer


class ToInternalValueMethod(TestCase):
    """Test deserialization is disabled."""

    def test_raises_error(self) -> None:
        """Verify the method raises a `NotImplementedError` error."""

        field = AuditlogFieldSerializer()
        with self.assertRaises(NotImplementedError) as cm:
            field.to_internal_value({"field": "value"})

        self.assertEqual(str(cm.exception), "Audit history is read-only.")
