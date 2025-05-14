"""Middleware for application-specific request/response processing.

Middleware are used to modify or enhance the request/response
cycle of incoming requests before they reach the application views or become
an outgoing client response.
"""

import uuid

from django.conf import settings
from django.http import HttpRequest

from .models import RequestLog

__all__ = ['LogRequestMiddleware']


class LogRequestMiddleware:
    """Log metadata from incoming HTTP requests to the database."""

    # __init__ signature required by Django for dependency injection
    def __init__(self, get_response: callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpRequest:
        """Execute the middleware on an incoming HTTP request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The processed request object.
        """

        cid = self._normalize_cid(request)
        response = self.get_response(request)

        request_log = RequestLog(
            method=request.method,
            endpoint=request.get_full_path(),
            response_code=response.status_code,
            remote_address=self._get_client_ip(request),
            cid=cid,
        )

        if not request.user.is_anonymous:
            request_log.user = request.user

        try:
            request_log.save()

        except Exception:
            pass

        return response

    @staticmethod
    def _normalize_cid(request: HttpRequest) -> str:
        """Extract the client CID and ensure it is a valid UUID.

        If a valid UUID is not set, a new is generated and set in
        the request header.

        Args:
            request: The incoming HTTP request.

        Returns:
            A tuple of (client_cid, final_cid).
        """

        # Convert a custom header name (e.g., "X-CID") into the format used by Django's request.META
        header_name = 'HTTP_' + settings.AUDITLOG_CID_HEADER.upper().replace('-', '_')
        cid = request.META.get(header_name)

        try:
            uuid.UUID(cid)

        except (ValueError, TypeError, Exception) as e:
            cid = str(uuid.uuid4())
            request.META[header_name] = cid

        return cid

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Return the client IP for the incoming request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The requesting IP address.
        """

        if x_forwarded_for := request.META.get('HTTP_X_FORWARDED_FOR'):
            return x_forwarded_for.split(',')[0]

        return request.META.get('REMOTE_ADDR')
