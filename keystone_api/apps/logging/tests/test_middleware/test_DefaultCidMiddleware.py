"""Unit tests for the `DefaultCidMiddleware` class."""

import uuid

from django.conf import settings
from django.http import HttpResponse
from django.test import override_settings, TestCase
from django.test.client import RequestFactory

from apps.logging.middleware import DefaultCidMiddleware


class DefaultCidAssignment(TestCase):
    """Test the generation of Default CID values."""

    def setUp(self) -> None:
        """Instantiate common testing fixtures."""

        self.rf = RequestFactory()
        self.middleware = DefaultCidMiddleware(lambda request: HttpResponse())

    @override_settings(AUDITLOG_CID_HEADER='X_CUSTOM_CID')
    def test_sets_default_cid_if_missing(self) -> None:
        """Verify a default CID is generated when the header is missing."""

        # Create a request without a CID
        request = self.rf.get('/some-path/')
        self.assertNotIn(settings.AUDITLOG_CID_HEADER, request.META)

        # Execute the response middleware
        response = self.middleware(request)
        cid = request.META.get('X_CUSTOM_CID')

        self.assertIsNotNone(cid)
        self.assertEqual(200, response.status_code)
        self.assertTrue(uuid.UUID(cid))  # Validates UUID hex format

    @override_settings(AUDITLOG_CID_HEADER='X_CUSTOM_CID')
    def test_preserves_existing_cid(self) -> None:
        """Verify an existing CID is not overwritten."""

        existing_cid = uuid.uuid4().hex
        request = self.rf.get('/some-path/')
        request.META['X_CUSTOM_CID'] = existing_cid

        self.middleware(request)
        self.assertEqual(existing_cid, request.META['X_CUSTOM_CID'])
