"""Unit tests for the `LogRequestMiddleware` class."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import override_settings, TestCase
from django.test.client import RequestFactory

from apps.logging.middleware import LogRequestMiddleware
from apps.logging.models import RequestLog


class LoggingToDatabase(TestCase):
    """Test the logging of requests to the database."""

    def test_authenticated_user(self) -> None:
        """Verify requests are logged for authenticated users."""

        rf = RequestFactory()
        request = rf.get('/hello/')
        request.user = get_user_model().objects.create()

        middleware = LogRequestMiddleware(lambda x: HttpResponse())
        middleware(request)

        self.assertEqual(RequestLog.objects.count(), 1)
        self.assertEqual(RequestLog.objects.first().user, request.user)

    def test_anonymous_user(self) -> None:
        """Verify requests are logged for anonymous users."""

        rf = RequestFactory()
        request = rf.get('/hello/')
        request.user = AnonymousUser()

        middleware = LogRequestMiddleware(lambda x: HttpResponse())
        middleware(request)

        self.assertEqual(RequestLog.objects.count(), 1)
        self.assertIsNone(RequestLog.objects.first().user)


class ClientIPLogging(TestCase):
    """Test the extraction and logging of client IP values from request headers."""

    def setUp(self) -> None:
        """Instantiate testing fixtures."""

        self.rf = RequestFactory()
        self.middleware = LogRequestMiddleware(lambda x: HttpResponse())

    def test_logs_ip_from_x_forwarded_for(self) -> None:
        """Verify the client IP is logged from the `X-Forwarded-For` header."""

        request = self.rf.get('/test-ip/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        request.META['REMOTE_ADDR'] = '192.168.2.2'
        request.user = AnonymousUser()

        self.middleware(request)
        log = RequestLog.objects.first()
        self.assertEqual(log.remote_address, '192.168.1.1')

    def test_logs_ip_from_remote_addr(self) -> None:
        """Verify the client IP is logged from `REMOTE_ADDR` when `X-Forwarded-For` is missing."""

        request = self.rf.get('/test-ip/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.user = AnonymousUser()

        self.middleware(request)
        log = RequestLog.objects.first()
        self.assertEqual(log.remote_address, '192.168.1.1')

    def test_logs_none_if_no_ip_headers(self) -> None:
        """Verify `None` is logged when no IP headers are present."""

        request = self.rf.get('/test-ip/')
        request.user = AnonymousUser()
        request.META.pop('REMOTE_ADDR', None)  # Explicitly remove default IP

        self.middleware(request)
        log = RequestLog.objects.first()
        self.assertIsNone(log.remote_address)


class CidLogging(TestCase):
    """Test the extraction and logging of CID values from request headers."""

    def setUp(self) -> None:
        """Instantiate testing fixtures."""

        self.rf = RequestFactory()
        self.middleware = LogRequestMiddleware(lambda x: HttpResponse())

    @override_settings(AUDITLOG_CID_HEADER='X_CUSTOM_CID')
    def test_cid_header_logged(self) -> None:
        """Verify the CID value is correctly extracted and saved."""

        cid_value = 'cid-12345'
        request = self.rf.get('/example/')
        request.META[settings.AUDITLOG_CID_HEADER] = cid_value

        request.user = AnonymousUser()

        self.middleware(request)
        log = RequestLog.objects.first()
        self.assertEqual(log.cid, cid_value)

    def test_missing_cid_header(self) -> None:
        """Verify CID is logged as `None` when the CID header is not present."""

        request = self.rf.get('/example/')
        request.user = AnonymousUser()
        self.middleware(request)

        log = RequestLog.objects.first()
        self.assertIsNone(log.cid)
