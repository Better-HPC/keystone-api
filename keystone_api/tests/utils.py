"""Custom testing utilities used to streamline common tests."""

from django.db import transaction
from django.test import Client


class CustomAsserts:
    """Custom assert methods for testing responses from REST endpoints."""

    client: Client
    assertEqual: callable  # Provided by TestCase class

    def assert_http_responses(self, endpoint: str, **kwargs) -> None:
        """Execute a series of API calls and assert the returned status matches the given values.

        Args:
            endpoint: The partial URL endpoint to perform requests against.
            **<request>: The integer status code expected by the given request type (get, post, etc.).
            **<request>_body: The data to include in the request (get_body, post_body, etc.).
            **<request>_headers: Header values to include in the request (get_headers, post_headers, etc.).
        """

        http_methods = ['get', 'head', 'options', 'post', 'put', 'patch', 'delete', 'trace']
        for method in http_methods:
            expected_status = kwargs.get(method, None)
            if expected_status is not None:
                self._assert_http_response(method, endpoint, expected_status, kwargs)

    def _assert_http_response(self, method: str, endpoint: str, expected_status: int, kwargs: dict):
        """Assert the HTTP response for a specific method matches the expected status.

        Args:
            method: The HTTP method to use (get, post, etc.).
            endpoint: The partial URL endpoint to perform requests against.
            expected_status: The integer status code expected by the given request type.
            kwargs: Additional keyword arguments for building the request.
        """

        http_callable = getattr(self.client, method)
        http_args = self._build_request_args(method, kwargs)

        # Preserve database state
        with transaction.atomic():
            request = http_callable(endpoint, **http_args)
            self.assertEqual(
                request.status_code, expected_status,
                f'{method.upper()} request received {request.status_code} instead of {expected_status} with content "{request.content}"')

            transaction.set_rollback(True)

    @staticmethod
    def _build_request_args(method: str, kwargs: dict) -> dict:
        """Isolate head and body arguments for a given HTTP method from a dict of arguments.

        Args:
            method: The HTTP method to identify arguments for.
            kwargs: A dictionary of arguments.

        Returns:
            A dictionary with formatted arguments.
        """

        arg_names = ('data', 'headers')
        arg_values = (kwargs.get(f'{method}_body', None), kwargs.get(f'{method}_headers', None))
        return {name: value for name, value in zip(arg_names, arg_values) if value is not None}
