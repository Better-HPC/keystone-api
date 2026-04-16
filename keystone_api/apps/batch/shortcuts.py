"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import json
import logging
import re
from typing import Any
from urllib.parse import urlencode

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import transaction
from django.urls import resolve, Resolver404
from rest_framework.test import APIRequestFactory, force_authenticate

from .exceptions import *

__all__ = [
    'execute_job',
    'resolve_references',
    'resolve_value',
    'traverse_dotpath'
]

logger = logging.getLogger(__name__)
factory = APIRequestFactory()

# Matches any @ref{alias.dotpath} token, capturing the `alias` and `dotpath`
_REF_PATTERN = re.compile(r'@ref\{([a-zA-Z0-9_]+)\.([^}]+)\}')


def traverse_dotpath(data: Any, dotpath: str, token: str) -> Any:
    """Walk a nested structure using a dot-separated path.

    Supports dictionary key access and integer-based list indexing.

    Args:
        data: The root object to traverse.
        dotpath: A dot-separated path string (e.g., `id` or `results.0.name`).
        token: The original reference token, used for error messages.

    Returns:
        The value found at the specified path.

    Raises:
        ReferenceResolutionError: If any segment of the path cannot be resolved.
    """

    current = data
    for segment in dotpath.split('.'):

        if isinstance(current, dict):
            if segment not in current:
                raise ReferenceResolutionError(token, f'Key "{segment}" not found in response')

            current = current[segment]

        elif isinstance(current, list):
            try:
                current = current[int(segment)]

            except (ValueError, IndexError):
                raise ReferenceResolutionError(token, f'Invalid list index "{segment}"')

        else:
            raise ReferenceResolutionError(
                token, f'Cannot traverse into {type(current).__name__} with "{segment}"'
            )

    return current


def lookup_alias(alias: str, dotpath: str, token: str, result_map: dict[str, dict]) -> Any:
    """Resolve a single alias and dotpath against the result map.

    Args:
        alias: The step alias to look up.
        dotpath: The dot-separated path into that step's response body.
        token: The original token string, used for error messages.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        The resolved value.

    Raises:
        ReferenceResolutionError: If the alias is unknown or the path cannot be traversed.
    """

    if alias not in result_map:
        raise ReferenceResolutionError(
            token, f'Alias "{alias}" has not been defined by a previous step'
        )

    return traverse_dotpath(result_map[alias], dotpath, token)


def resolve_value(value: Any, result_map: dict[str, dict]) -> Any:
    """Resolve a single value, substituting any `@ref` tokens.

    When the entire string is a single token, the resolved value is returned
    directly so that non-string types (int, bool, list, ...) are preserved.
    When the token is embedded within surrounding text, it is resolved,
    stringified, and substituted in place.

    Non-string values and strings with no `@ref` tokens are returned
    unchanged.

    Args:
        value: The value to inspect and potentially resolve.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        The resolved value, or the original value if no token was found.

    Raises:
        ReferenceResolutionError: If the reference target cannot be found.
    """

    if not isinstance(value, str) or '@ref{' not in value:
        return value

    matches = list(_REF_PATTERN.finditer(value))
    if not matches:
        return value

    # Whole-value: the single token spans the entire string.
    # Return the resolved value directly to preserve its original type.
    if len(matches) == 1 and matches[0].group(0) == value:
        m = matches[0]
        return lookup_alias(m.group(1), m.group(2), m.group(0), result_map)

    # Embedded: one or more tokens sit within surrounding text.
    # Resolve each token to a string and substitute it in place.
    def _replace(m: re.Match) -> str:
        resolved = lookup_alias(m.group(1), m.group(2), m.group(0), result_map)
        return str(resolved)

    return _REF_PATTERN.sub(_replace, value)


def resolve_references(data: Any, result_map: dict[str, dict]) -> Any:
    """Recursively resolve all `@ref` tokens within a data structure.

    Walks dictionaries, lists, and scalar values. String values are
    inspected for `@ref` tokens and resolved. Non-matching values pass
    through unchanged.

    Args:
        data: The payload structure to resolve. May be a dict, list, or scalar.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        A new data structure with all references substituted.

    Raises:
        ReferenceResolutionError: If any reference cannot be resolved.
    """

    if isinstance(data, dict):
        return {key: resolve_references(value, result_map) for key, value in data.items()}

    if isinstance(data, list):
        return [resolve_references(item, result_map) for item in data]

    return resolve_value(data, result_map)


def _build_request(
    method: str,
    path: str,
    payload: dict,
    query_params: dict,
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
):
    """Construct a DRF request object from step parameters.

    The server hostname Should match the host of the outer incoming
    request so that URLs constructed internally (e.g. pagination links)
    are valid.

    Args:
        method: The HTTP method to use.
        path: The URL path to request.
        payload: The JSON body for the request.
        query_params: Query string parameters.
        user: An optional authenticated user to attach to the request.
        server_name: The server hostname to set on the request.

    Returns:
        A DRF-compatible request object.
    """

    if query_params:
        qs = urlencode(query_params, doseq=True)
        path = f'{path}?{qs}'

    kwargs = {'content_type': 'application/json', 'SERVER_NAME': server_name}

    if method in ('GET', 'DELETE', 'HEAD', 'OPTIONS'):
        request = factory.generic(method, path, **kwargs)

    else:
        request = factory.generic(method, path, data=json.dumps(payload or {}), **kwargs)

    if user is not None and user.is_authenticated:
        force_authenticate(request, user=user)

    return request


def _invoke_view(request, path: str) -> tuple[int, dict | None]:
    """Resolve a URL path and invoke the matched view.

    Args:
        request: The reconstructed DRF request.
        path: The URL path to resolve (without query string).

    Returns:
        A tuple of (status_code, response_body).
    """

    try:
        match = resolve(path)

    except Resolver404:
        return 404, {'detail': f'No route matched: {path}'}

    view = match.func

    # Initialise the view if it's a class-based view (ViewSet / APIView)
    if hasattr(view, 'initkwargs'):
        view.cls.kwargs = match.kwargs

    response = view(request, *match.args, **match.kwargs)

    # Force rendering so response.data is populated
    if hasattr(response, 'render'):
        response.render()

    if hasattr(response, 'data'):
        return response.status_code, response.data

    if hasattr(response, 'content'):
        try:
            return response.status_code, json.loads(response.content)

        except (json.JSONDecodeError, TypeError):
            return response.status_code, {'raw': response.content.decode('utf-8', errors='replace')}

    return response.status_code, None


def execute_step(
    method: str,
    path: str,
    payload: dict,
    query_params: dict,
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
) -> tuple[int, dict]:
    """Execute a single step and return its result.

    Args:
        method: The HTTP method.
        path: The URL path.
        payload: The resolved JSON body.
        query_params: Query string parameters.
        user: An optional authenticated user to attach to the request.
        server_name: The server hostname to set on the request.

    Returns:
        A tuple of (status_code, response_body).
    """

    request = _build_request(method, path, payload, query_params, user=user, server_name=server_name)
    clean_path = path.split('?')[0]
    return _invoke_view(request, clean_path)


def execute_job(
    steps: list[dict],
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
    dry_run: bool = False,
) -> list[dict]:
    """Execute a list of steps inside a single database transaction.

    Each step dict may contain:
        - `ref` (str, optional): An alias for referencing this step's output.
        - `method` (str): The HTTP method.
        - `path` (str): The URL path.
        - `payload` (dict, optional): The JSON body.
        - `query_params` (dict, optional): Query string parameters.

    Path and payload values matching the `@ref{alias.dotpath}` pattern are
    resolved against the response bodies of previously executed steps.
    References are optional and steps without them behave identically to
    plain requests.

    All steps execute sequentially within a `transaction.atomic()` block.
    If any step fails, the entire transaction is rolled back. When
    `dry_run=True`, the transaction is always rolled back after all steps
    complete successfully, leaving the database unchanged.

    Args:
        steps: An ordered list of step descriptors.
        user: An optional authenticated user to run as during each sub-request.
        server_name: The hostname of the outer incoming request.
        dry_run: When `True`, all steps are executed but database state is not persisted.

    Returns:
        A list of dictionaries containing the outcome of each executed step.

    Raises:
        JobExecutionError: If any step returns a 4xx/5xx status code.
        ReferenceResolutionError: If a symbolic reference cannot be resolved.
    """

    result_map = {}
    results = []

    try:
        with transaction.atomic():
            for index, step in enumerate(steps, start=1):
                ref = step.get('ref', '')
                method = step['method'].upper()
                path = step['path']
                payload = step.get('payload', {})
                query_params = step.get('query_params', {})

                # Resolve symbolic references in the path and payload
                resolved_path = resolve_references(path, result_map)
                resolved_payload = resolve_references(payload, result_map)

                logger.info('Executing job step %s: %s %s', index, method, resolved_path)
                status_code, body = execute_step(
                    method, resolved_path, resolved_payload, query_params,
                    user=user, server_name=server_name,
                )

                results.append({
                    'ref': ref or None,
                    'index': index,
                    'method': method,
                    'path': resolved_path,
                    'status': status_code,
                    'body': body,
                })

                # Register in result map if the step has a ref alias
                if ref:
                    result_map[ref] = body

                if status_code >= 400:
                    raise JobExecutionError(index, method, resolved_path, status_code, body)

            if dry_run:
                # Force exit the DB transaction without committing
                raise DryRunRollbackError

    except DryRunRollbackError:
        pass

    return results
