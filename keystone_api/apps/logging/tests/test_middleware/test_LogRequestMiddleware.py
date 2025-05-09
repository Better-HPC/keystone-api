"""Unit tests for the `LogRequestMiddleware` class."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
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


class ClientIPMethod(TestCase):
    """Test fetching the client IP via the `get_client_ip` method."""

    def test_ip_with_x_forwarded_for(self) -> None:
        """Verify IP data is fetched from the `HTTP_X_FORWARDED_FOR` header."""

        request = HttpRequest()

        # The `HTTP_X_FORWARDED_FOR` header should take precedence over `REMOTE_ADDR`
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        request.META['REMOTE_ADDR'] = '192.168.2.2'

        client_ip = LogRequestMiddleware.get_client_ip(request)
        self.assertEqual(client_ip, '192.168.1.1')

    def test_ip_with_remote_addr(self) -> None:
        """Verify IP data is fetched from the `REMOTE_ADDR` header."""

        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        client_ip = LogRequestMiddleware.get_client_ip(request)
        self.assertEqual(client_ip, '192.168.1.1')

    def test_ip_without_headers(self) -> None:
        """Verify the returned IP value is `None` when no headers are specified."""

        request = HttpRequest()
        client_ip = LogRequestMiddleware.get_client_ip(request)
        self.assertIsNone(client_ip)


class CidLogging(TestCase):
    """Test extraction and logging of CID from request headers."""

    def setUp(self) -> None:
        """Create a dummy request and define header values."""

        self.rf = RequestFactory()
        self.middleware = LogRequestMiddleware(lambda x: HttpResponse())
        self.cid_header = 'HTTP_X_CUSTOM_CID'
        self.cid_value = 'cid-12345'

    @override_settings(AUDITLOG_CID_HEADER='HTTP_X_CUSTOM_CID')
    def test_cid_header_logged(self) -> None:
        """Verify the CID value is correctly extracted and saved."""

        request = self.rf.get('/example/', **{self.cid_header: self.cid_value})
        request.user = AnonymousUser()
        self.middleware(request)

        log = RequestLog.objects.first()
        self.assertEqual(log.cid, self.cid_value)

    @override_settings(AUDITLOG_CID_HEADER='HTTP_X_CUSTOM_CID')
    def test_missing_cid_header(self) -> None:
        """Verify CID is None when the header is not present."""

        request = self.rf.get('/example/')
        request.user = AnonymousUser()
        self.middleware(request)

        log = RequestLog.objects.first()
        self.assertIsNone(log.cid)
