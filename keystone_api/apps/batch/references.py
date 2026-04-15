"""Symbolic reference resolution for batch job payloads.

Provides utilities for resolving forward references between steps
within a single batch job. References use the ``@ref:<alias>.<dotpath>``
syntax, where ``<alias>`` identifies a previously executed step and
``<dotpath>`` navigates into that step's response body.

References are optional. Payloads without ``@ref:`` tokens pass
through unchanged.
"""

import re
from typing import Any

from apps.batch.exceptions import ReferenceResolutionError

__all__ = ['resolve_references']

# Matches the full @ref:alias.dot.path pattern
_REF_PATTERN = re.compile(r'^@ref:([a-zA-Z0-9_]+)\.(.+)$')


def _traverse(data: Any, dotpath: str, token: str) -> Any:
    """Walk a nested structure using a dot-separated path.

    Supports dictionary key access and integer-based list indexing.

    Args:
        data: The root object to traverse.
        dotpath: A dot-separated path string (e.g., ``id`` or ``results.0.name``).
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


def _resolve_value(value: Any, result_map: dict[str, dict]) -> Any:
    """Resolve a single value, substituting any symbolic reference.

    If the value is a string matching the ``@ref:`` pattern, it is
    resolved against the result map. All other values are returned
    unchanged.

    Args:
        value: The value to inspect and potentially resolve.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        The resolved value, or the original value if no reference was found.

    Raises:
        ReferenceResolutionError: If the reference syntax is valid but the target cannot be found.
    """

    if not isinstance(value, str):
        return value

    match = _REF_PATTERN.match(value)
    if not match:
        return value

    alias, dotpath = match.groups()
    token = value

    if alias not in result_map:
        raise ReferenceResolutionError(
            token, f'Alias "{alias}" has not been defined by a previous step'
        )

    return _traverse(result_map[alias], dotpath, token)


def resolve_references(data: Any, result_map: dict[str, dict]) -> Any:
    """Recursively resolve all symbolic references within a data structure.

    Walks dictionaries, lists, and scalar values. String values matching
    the ``@ref:<alias>.<dotpath>`` pattern are replaced with the resolved
    value from the result map. Non-matching values pass through unchanged.

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

    return _resolve_value(data, result_map)
