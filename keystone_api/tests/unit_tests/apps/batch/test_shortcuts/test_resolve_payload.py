"""Unit tests for the `resolve_payload` function."""

from unittest.mock import Mock

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import resolve_payload


class RecursiveContainerWalking(TestCase):
    """Test that `resolve_payload` walks dicts, lists, and nested structures recursively."""

    def test_resolves_dict_values_recursively(self) -> None:
        """Verify all token-containing string values in a dict are resolved."""

        result_map = {'s': {'id': 5}}
        data = {'url': '/things/@ref{s.id}/', 'static': 'hello'}
        result = resolve_payload(data, result_map)
        self.assertEqual({'url': '/things/5/', 'static': 'hello'}, result)

    def test_resolves_list_items_recursively(self) -> None:
        """Verify token-containing items inside a list are resolved."""

        result_map = {'s': {'val': 'x'}}
        result = resolve_payload(['@ref{s.val}', 'literal'], result_map)
        self.assertEqual(['x', 'literal'], result)

    def test_resolves_nested_structure(self) -> None:
        """Verify tokens nested inside dicts within lists are resolved."""

        result_map = {'s': {'name': 'Alice'}}
        data = {'users': [{'name': '@ref{s.name}'}]}
        result = resolve_payload(data, result_map)
        self.assertEqual('Alice', result['users'][0]['name'])

    def test_raises_on_unresolvable_token_in_nested_structure(self) -> None:
        """Verify an unresolvable token deep in the structure raises `ReferenceResolutionError`."""

        data = {'outer': {'inner': ['@ref{ghost.id}']}}
        with self.assertRaises(ReferenceResolutionError):
            resolve_payload(data, {})


class RefTokenResolution(TestCase):
    """Test the resolution of `@ref` tokens within containers."""

    def test_resolves_ref_token_in_dict_value(self) -> None:
        """Verify a `@ref` token inside a dict value is resolved to the referenced value."""

        result_map = {'s': {'id': 5}}
        result = resolve_payload({'id': '@ref{s.id}'}, result_map)
        self.assertEqual({'id': 5}, result)

    def test_resolves_ref_token_in_list_item(self) -> None:
        """Verify a `@ref` token inside a list item is resolved to the referenced value."""

        result_map = {'s': {'val': 42}}
        result = resolve_payload(['@ref{s.val}'], result_map)
        self.assertEqual([42], result)


class FileTokenResolution(TestCase):
    """Test the resolution of `@file` tokens within containers."""

    def test_resolves_file_token_in_dict(self) -> None:
        """Verify a `@file` token inside a dict value resolves to the uploaded object."""

        upload = Mock()
        data = {'attachment': '@file{doc}', 'name': 'cover'}
        result = resolve_payload(data, {}, files={'doc': upload})

        self.assertIs(result['attachment'], upload, 'File token should resolve to uploaded object')
        self.assertEqual('cover', result['name'])


class PassthroughBehaviour(TestCase):
    """Test that non-token values pass through `resolve_payload` unchanged."""

    def test_integer_passthrough(self) -> None:
        """Verify integer values pass through unchanged."""

        self.assertEqual(123, resolve_payload(123, {}))

    def test_dict_passthrough(self) -> None:
        """Verify values nested inside a dictionary pass through unchanged."""

        data = {'string': 'abc', 'int': 5, 'bool': True, 'none': None, 'list': [1, 2]}
        result = resolve_payload(data, {})
        self.assertEqual(data, result)

    def test_empty_dict_passthrough(self) -> None:
        """Verify an empty dict resolves to an empty dict."""

        self.assertEqual({}, resolve_payload({}, {}))

    def test_list_passthrough(self) -> None:
        """Verify values nested inside a list pass through unchanged."""

        data = ['abc', 5, True, None, [1, 2]]
        result = resolve_payload(data, {})
        self.assertEqual(data, result)

    def test_empty_list_passthrough(self) -> None:
        """Verify an empty list resolves to an empty list."""

        self.assertEqual([], resolve_payload([], {}))

    def test_none_passthrough(self) -> None:
        """Verify `None` values resolve to `None`."""

        self.assertEqual(None, resolve_payload(None, {}))
