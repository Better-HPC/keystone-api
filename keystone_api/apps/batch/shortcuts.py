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
from django.test.client import BOUNDARY, encode_multipart, MULTIPART_CONTENT
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

_TOKEN_PATTERN = re.compile(r'@(file|ref)\{([^}]*)\}')
_LABEL_PATTERNS = {
    'file': re.compile(r'^[a-zA-Z0-9_]+$'),
    'ref': re.compile(r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9_.]+$')
}


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


def _resolve_token(match: re.Match, result_map: dict[str, dict], files: dict | None) -> Any:
    """Resolve a single matched `@file` or `@ref` token to its target value.

    Args:
        match: The regex match for the token.
        result_map: A mapping of step aliases to their response bodies.
        files: An optional mapping of part names to uploaded file objects.

    Returns:
        The resolved value (file object or referenced data).

    Raises:
        ReferenceResolutionError: If the token body is malformed or the target cannot be found.
    """

    token, kind, body = match.group(0), match.group(1), match.group(2)

    pattern = _LABEL_PATTERNS[kind]
    if not pattern.match(body):
        raise ReferenceResolutionError(token, 'Reference labels may only contain letters, numbers, and underscores')

    if kind == 'file':
        if not files or body not in files:
            raise ReferenceResolutionError(token, f'File part "{body}" was not uploaded with this request')

        return files[body]

    alias, dotpath = body.split('.', 1)
    return lookup_alias(alias, dotpath, token, result_map)


def resolve_value(value: str, result_map: dict[str, dict], files: dict | None = None) -> Any:
    """Resolve a single value, substituting any `@ref` or `@file` tokens.

    When the entire string is a single `@ref` token, the resolved value is
    returned directly so that non-string types (int, bool, list, ...) are
    preserved. When the token is embedded within surrounding text, it is
    resolved, stringified, and substituted in place.

    When the entire string is a single `@file` token, the corresponding file
    object is returned directly from the files dict.

    Non-string values and strings with no recognized tokens are returned
    unchanged.

    Args:
        value: The value to inspect and potentially resolve.
        result_map: A mapping of step aliases to their response bodies.
        files: An optional mapping of part names to uploaded file objects.

    Returns:
        The resolved value, or the original value if no token was found.

    Raises:
        ReferenceResolutionError: If a token is malformed or the reference target cannot be found.
    """

    tokens = list(_TOKEN_PATTERN.finditer(value))
    if not tokens:
        return value

    # Whole-value single token: return the resolved value directly to preserve its type
    if len(tokens) == 1 and tokens[0].group(0) == value:
        return _resolve_token(tokens[0], result_map, files)

    # Embedded tokens: resolve each to a string and substitute in place
    return _TOKEN_PATTERN.sub(lambda m: str(_resolve_token(m, result_map, files)), value)


def resolve_references(data: Any, result_map: dict[str, dict], files: dict | None = None) -> Any:
    """Recursively resolve all `@ref` and `@file` tokens within a data structure.

    Walks dictionaries, lists, and scalar values. String values are
    inspected for `@ref` and `@file` tokens and resolved. Non-matching
    values pass through unchanged.

    Args:
        data: The payload structure to resolve. May be a dict, list, or scalar.
        result_map: A mapping of step aliases to their response bodies.
        files: An optional mapping of part names to uploaded file objects.

    Returns:
        A new data structure with all references substituted.

    Raises:
        ReferenceResolutionError: If any reference cannot be resolved.
    """

    if isinstance(data, dict):
        return {key: resolve_references(value, result_map, files) for key, value in data.items()}

    if isinstance(data, list):
        return [resolve_references(item, result_map, files) for item in data]

    if isinstance(data, str):
        return resolve_value(data, result_map, files)

    return data


def _payload_has_files(payload: Any) -> bool:
    """Return whether a resolved payload contains any file objects.

    Args:
        payload: The resolved payload structure to inspect.

    Returns:
        True if any value within the payload is a file-like object.
    """

    if isinstance(payload, dict):
        return any(_payload_has_files(v) for v in payload.values())

    if isinstance(payload, list):
        return any(_payload_has_files(item) for item in payload)

    return hasattr(payload, 'read')


def build_request(
    method: str,
    path: str,
    payload: dict,
    query_params: dict,
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
):
    """Construct a DRF request object from step parameters.

    When the resolved payload contains file objects the request is built as
    multipart/form-data. Otherwise, it is sent as application/json.

    The server hostname should match the host of the outer incoming request
    so that URLs constructed internally (e.g. pagination links) are valid.

    Args:
        method: The HTTP method to use.
        path: The URL path to request.
        payload: The resolved JSON body, potentially containing file objects.
        query_params: Query string parameters.
        user: An optional authenticated user to attach to the request.
        server_name: The server hostname to set on the request.

    Returns:
        A DRF-compatible request object.
    """

    if query_params:
        path = f'{path}?{urlencode(query_params, doseq=True)}'

    if _payload_has_files(payload):
        data = encode_multipart(BOUNDARY, payload)
        content_type = MULTIPART_CONTENT

    else:
        data = json.dumps(payload or {})
        content_type = 'application/json'

    request = factory.generic(method, path, data=data, content_type=content_type, SERVER_NAME=server_name)

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
        payload: The resolved JSON body, potentially containing file objects.
        query_params: Query string parameters.
        user: An optional authenticated user to attach to the request.
        server_name: The server hostname to set on the request.

    Returns:
        A tuple of (status_code, response_body).
    """

    request = build_request(method, path, payload, query_params, user=user, server_name=server_name)
    clean_path = path.split('?')[0]
    return _invoke_view(request, clean_path)


def execute_job(
    steps: list[dict],
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
    dry_run: bool = False,
    files: dict | None = None,
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
    Payload values matching the `@file{name}` pattern are resolved against
    the provided files dict. References are optional and steps without them
    behave identically to plain requests.

    All steps execute sequentially within a `transaction.atomic()` block.
    If any step fails, the entire transaction is rolled back. When
    `dry_run=True`, the transaction is always rolled back after all steps
    complete successfully, leaving the database unchanged.

    Args:
        steps: An ordered list of step descriptors.
        user: An optional authenticated user to run as during each sub-request.
        server_name: The hostname of the outer incoming request.
        dry_run: When `True`, all steps are executed but database state is not persisted.
        files: An optional mapping of part names to uploaded file objects.

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
                ref = step.get('ref')
                method = step['method'].upper()
                path = step['path']
                payload = step.get('payload', {})
                query_params = step.get('query_params', {})

                # Resolve symbolic references in the path and payload
                resolved_path = resolve_references(path, result_map, files)
                resolved_payload = resolve_references(payload, result_map, files)

                logger.info('Executing job step %s: %s %s', index, method, resolved_path)
                status_code, body = execute_step(
                    method, resolved_path, resolved_payload, query_params,
                    user=user, server_name=server_name,
                )

                results.append({
                    'ref': ref,
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
