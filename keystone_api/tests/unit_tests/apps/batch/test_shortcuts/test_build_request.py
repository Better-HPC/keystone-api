"""Unit tests for the `build_request` function."""

import io
import json
from unittest.mock import Mock

from django.test import TestCase
from django.test.client import MULTIPART_CONTENT

from apps.batch.shortcuts import build_request


class ContentTypeSelection(TestCase):
    """Test the content-type chosen based on whether the payload contains file objects."""

    def test_json_payload_sets_json_content_type(self) -> None:
        """Verify a payload with no file objects is sent as application/json."""

        request = build_request('POST', '/items/', {'name': 'x'}, {})

        self.assertEqual(request.META['CONTENT_TYPE'], 'application/json')
        self.assertEqual(json.loads(request.body), {'name': 'x'})

    def test_multipart_payload_sets_multipart_content_type(self) -> None:
        """Verify a payload containing a file object is sent as multipart/form-data."""

        upload = io.BytesIO(b'binary-content')
        upload.name = 'sample.txt'
        request = build_request('POST', '/items/', {'file': upload, 'name': 'x'}, {})

        self.assertEqual(request.META['CONTENT_TYPE'], MULTIPART_CONTENT)

    def test_empty_payload_serialized_as_empty_object(self) -> None:
        """Verify an empty payload is serialized as an empty JSON object."""

        request = build_request('POST', '/items/', {}, {})

        self.assertEqual(request.body, b'{}')

    def test_none_payload_serialized_as_empty_object(self) -> None:
        """Verify a `None` payload is serialized as an empty JSON object."""

        request = build_request('POST', '/items/', None, {})

        self.assertEqual(request.body, b'{}')


class QueryParamEncoding(TestCase):
    """Test the encoding of query parameters onto the request path."""

    def test_query_params_appended_to_path(self) -> None:
        """Verify query params are URL-encoded and appended to the request path."""

        request = build_request('GET', '/items/', {}, {'page': 2, 'size': 10})

        self.assertEqual('page=2&size=10', request.META['QUERY_STRING'])

    def test_query_list_formatting(self) -> None:
        """Verify list-valued query params are encoded as a CSV."""

        request = build_request('GET', '/items/', {}, {'tag': ['a', 'b']})

        query_string = request.META['QUERY_STRING']
        self.assertIn('tag=a,b', query_string)


class AuthenticationAttachment(TestCase):
    """Test the attachment of authenticated users to the constructed request."""

    def test_authenticated_user_is_attached(self) -> None:
        """Verify an authenticated user is associated with the request."""

        user = Mock()
        user.is_authenticated = True
        request = build_request('GET', '/items/', {}, {}, user=user)

        self.assertIs(request._force_auth_user, user)

    def test_unauthenticated_user_is_not_attached(self) -> None:
        """Verify unauthenticated users are not associated with the request."""

        anonymous = Mock()
        anonymous.is_authenticated = False
        request = build_request('GET', '/items/', {}, {}, user=anonymous)

        # Forced authentication sets `_force_auth_user`.
        # The attribute's absence indicates no auth was forced
        self.assertFalse(hasattr(request, '_force_auth_user'))

    def test_none_user_is_not_attached(self) -> None:
        """Verify a `None` user results in no user being associated with the request."""

        request = build_request('GET', '/items/', {}, {}, user=None)

        self.assertFalse(hasattr(request, '_force_auth_user'))


class ServerNameApplication(TestCase):
    """Test the application of the server_name argument to the constructed request."""

    def test_server_name_is_applied(self) -> None:
        """Verify the server_name argument sets the request HTTP_HOST/SERVER_NAME."""

        request = build_request('GET', '/items/', {}, {}, server_name='api.example.com')

        self.assertEqual(request.META['SERVER_NAME'], 'api.example.com')