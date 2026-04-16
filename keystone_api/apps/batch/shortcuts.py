"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import json
import logging
from urllib.parse import urlencode

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import transaction
from django.urls import resolve, Resolver404
from rest_framework.test import APIRequestFactory, force_authenticate

from .exceptions import *
from .references import *

__all__ = ['execute_job']

logger = logging.getLogger(__name__)
factory = APIRequestFactory()


def _build_request(
    method: str,
    path: str,
    payload: dict,
    query_params: dict,
    user: AbstractBaseUser | None = None,
    server_name: str = 'localhost',
):
    """Construct a DRF request object from step parameters.

    Args:
        method: The HTTP method to use.
        path: The URL path to request.
        payload: The JSON body for the request.
        query_params: Query string parameters.
        user: An optional authenticated user to attach to the request.
        server_name: The server hostname to set on the request. Should match
            the host of the outer incoming request so that URLs constructed
            internally (e.g. pagination links) are valid.

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


def _invoke_view(request, path: str) -> tuple[int, dict]:
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


def _execute_step(
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

    Path and payload values matching the ``@ref{alias.dotpath}`` pattern are
    resolved against the response bodies of previously executed steps.
    References are optional -- steps without them behave identically to
    plain requests.

    All steps execute sequentially within a ``transaction.atomic()`` block.
    If any step fails, the entire transaction is rolled back. When
    ``dry_run=True``, the transaction is always rolled back after all steps
    complete successfully, leaving the database unchanged.

    Args:
        steps: An ordered list of step descriptors.
        user: An optional authenticated user whose identity will be forwarded
            to each sub-request. When provided, all internal requests are
            force-authenticated as this user, avoiding 401 responses from
            endpoints that require authentication.
        server_name: The hostname of the outer incoming request, used to
            construct the internal sub-requests. Defaults to 'localhost'.
            Pass ``request.get_host()`` from the outer view to ensure
            sub-request URLs are valid in all deployment configurations.
        dry_run: When ``True``, all steps are executed and their results
            returned, but the transaction is rolled back so no changes are
            persisted to the database.

    Returns:
        A tuple of (JobStatus, results) where results is a list of
        dicts containing the outcome of each executed step.

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
                status_code, body = _execute_step(
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
                raise DryRunRollbackError

    except DryRunRollbackError:
        pass

    return results
