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


class DefaultCidMiddleware:
    """Assign a default CID value when not provided by the client in the request header.

    See the `AUDITLOG_CID_HEADER` setting for the header name used to store CID values.
    """

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

        request.META.setdefault(settings.AUDITLOG_CID_HEADER, uuid.uuid4().hex)
        return self.get_response(request)


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

        response = self.get_response(request)
        request_log = RequestLog(
            method=request.method,
            endpoint=request.get_full_path(),
            response_code=response.status_code,
            remote_address=self.get_client_ip(request),
            cid=request.META.get(settings.AUDITLOG_CID_HEADER)
        )

        if not request.user.is_anonymous:
            request_log.user = request.user

        request_log.save()
        return response

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Return the client IP for the incoming request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The requesting IP address.
        """

        if x_forwarded_for := request.META.get('HTTP_X_FORWARDED_FOR'):
            return x_forwarded_for.split(',')[0]

        else:
            return request.META.get('REMOTE_ADDR')
