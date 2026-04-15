"""Symbolic reference resolution for batch job payloads.

Provides utilities for resolving forward references between steps
within a single batch job. References use the ``@ref{<alias>.<dotpath>}``
syntax, where ``<alias>`` identifies a previously executed step and
``<dotpath>`` navigates into that step's response body.

References may appear in two positions:

* **Whole-value** -- the entire string is a single token::

      "@ref{create_user.id}"

  The resolved value is returned as-is, preserving its original type
  (int, bool, list, ...). Use this form inside JSON payloads or
  ``query_params`` values where type fidelity matters.

* **Embedded** -- the token appears within a larger string::

      "/users/@ref{create_user.id}/profile/"

  The token is resolved, coerced to a string, and substituted in place.
  Use this form inside URL paths or any field where static text surrounds
  the reference.

References are optional. Values that contain no ``@ref{`` tokens pass
through unchanged.
"""

import re
from typing import Any

from apps.batch.exceptions import ReferenceResolutionError

__all__ = ['resolve_references']

# Matches any @ref{alias.dotpath} token, anchored or embedded.
# Capturing groups: (alias, dotpath)
_REF_PATTERN = re.compile(r'@ref\{([a-zA-Z0-9_]+)\.([^}]+)\}')


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


def _lookup(alias: str, dotpath: str, token: str, result_map: dict[str, dict]) -> Any:
    """Resolve a single alias and dotpath against the result map.

    Args:
        alias: The step alias to look up.
        dotpath: The dot-separated path into that step's response body.
        token: The original token string, used for error messages.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        The resolved value.

    Raises:
        ReferenceResolutionError: If the alias is unknown or the path cannot
            be traversed.
    """

    if alias not in result_map:
        raise ReferenceResolutionError(
            token, f'Alias "{alias}" has not been defined by a previous step'
        )

    return _traverse(result_map[alias], dotpath, token)


def _resolve_value(value: Any, result_map: dict[str, dict]) -> Any:
    """Resolve a single value, substituting any ``@ref:`` tokens.

    When the entire string is a single token, the resolved value is returned
    directly so that non-string types (int, bool, list, ...) are preserved.
    When the token is embedded within surrounding text, it is resolved,
    stringified, and substituted in place.

    Non-string values and strings with no ``@ref:`` tokens are returned
    unchanged.

    Args:
        value: The value to inspect and potentially resolve.
        result_map: A mapping of step aliases to their response bodies.

    Returns:
        The resolved value, or the original value if no token was found.

    Raises:
        ReferenceResolutionError: If the reference syntax is valid but the
            target cannot be found.
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
        return _lookup(m.group(1), m.group(2), m.group(0), result_map)

    # Embedded: one or more tokens sit within surrounding text.
    # Resolve each token to a string and substitute it in place.
    def _replace(m: re.Match) -> str:
        resolved = _lookup(m.group(1), m.group(2), m.group(0), result_map)
        return str(resolved)

    return _REF_PATTERN.sub(_replace, value)


def resolve_references(data: Any, result_map: dict[str, dict]) -> Any:
    """Recursively resolve all ``@ref:`` tokens within a data structure.

    Walks dictionaries, lists, and scalar values. String values are
    inspected for ``@ref:`` tokens and resolved via :func:`_resolve_value`.
    Non-matching values pass through unchanged.

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
