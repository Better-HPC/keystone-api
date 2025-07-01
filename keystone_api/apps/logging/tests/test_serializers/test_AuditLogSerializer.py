"""Unittests for the `AuditLogSerializer` class."""

from unittest.mock import Mock

from django.test import TestCase

from apps.logging.models import AuditLog
from apps.logging.serializers import AuditLogSerializer


class GetRecordNameMethod(TestCase):
    """Test the generation of record names."""

    def test_record_name_format(self):
        """Verify record names include the app label and class name in the expected format."""

        mock_model_class = Mock(__name__='TestModel')
        mock_content_type = Mock()
        mock_content_type.app_label = 'test_app'
        mock_content_type.model_class.return_value = mock_model_class

        mock_audit_log = Mock(spec=AuditLog)
        mock_audit_log.content_type = mock_content_type

        serializer = AuditLogSerializer()
        record_name = serializer.get_record_name(mock_audit_log)

        self.assertEqual('test_app | TestModel', record_name)
