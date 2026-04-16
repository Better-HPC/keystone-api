"""Unit tests for the `resolve_references` function."""

from django.test import TestCase

from apps.batch.shortcuts import resolve_references


class ResolveReferencesFunction(TestCase):
    """Test the resolution of `@ref` tokens within a data structure"""

    def test_resolves_dict_values_recursively(self) -> None:
        """Verify all token-containing string values in a dict are resolved."""

        result_map = {'s': {'id': 5}}
        data = {'url': '/things/@ref{s.id}/', 'static': 'hello'}
        result = resolve_references(data, result_map)
        self.assertEqual(result, {'url': '/things/5/', 'static': 'hello'})

    def test_resolves_list_items_recursively(self) -> None:
        """Verify token-containing items inside a list are resolved."""

        result_map = {'s': {'val': 'x'}}
        result = resolve_references(['@ref{s.val}', 'literal'], result_map)
        self.assertEqual(result, ['x', 'literal'])

    def test_resolves_nested_structure(self) -> None:
        """Verify tokens nested inside dicts within lists are resolved."""

        result_map = {'s': {'name': 'Alice'}}
        data = {'users': [{'name': '@ref{s.name}'}]}
        result = resolve_references(data, result_map)
        self.assertEqual(result['users'][0]['name'], 'Alice')

    def test_scalar_passthrough(self) -> None:
        """Verify scalar values with no token pass through unchanged."""

        self.assertEqual(resolve_references(123, {}), 123)

    def test_empty_dict_passthrough(self) -> None:
        """Verify an empty dict resolves to an empty dict."""

        self.assertEqual(resolve_references({}, {}), {})

    def test_empty_list_passthrough(self) -> None:
        """Verify an empty list resolves to an empty list."""

        self.assertEqual(resolve_references([], {}), [])
