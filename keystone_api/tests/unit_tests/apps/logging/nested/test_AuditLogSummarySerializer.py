"""Unit tests for the `AuditLogSummarySerializer` class."""

from django.test import TestCase

from apps.logging.models import AuditLog
from apps.logging.nested import AuditLogSummarySerializer


class GetActionMethod(TestCase):
    """Test the casting of action types to strings by the `get_action` method."""

    def setUp(self) -> None:
        """Instantiate a serializer instance."""

        self.serializer = AuditLogSummarySerializer()

    def test_returns_create_string_for_create_action(self) -> None:
        """Verify the action string for CREATE action."""

        mock_obj = type('MockAuditLog', (), {'action': AuditLog.Action.CREATE})()

        result = self.serializer.get_action(mock_obj)

        self.assertEqual("create", result)

    def test_returns_update_string_for_update_action(self) -> None:
        """Verify the action string for UPDATE action."""

        mock_obj = type('MockAuditLog', (), {'action': AuditLog.Action.UPDATE})()

        result = self.serializer.get_action(mock_obj)

        self.assertEqual("update", result)

    def test_returns_delete_string_for_delete_action(self) -> None:
        """Verify the action string for DELETE action."""

        mock_obj = type('MockAuditLog', (), {'action': AuditLog.Action.DELETE})()

        result = self.serializer.get_action(mock_obj)

        self.assertEqual("delete", result)
