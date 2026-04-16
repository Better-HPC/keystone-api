"""Unit tests for the `resolve_value` function."""

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import resolve_value


class ResolveValueMethod(TestCase):
    """Test the formatting of valuse with @ref placeholders."""

    def test_returns_non_string_unchanged(self) -> None:
        """Verify integer values pass through without modification."""

        self.assertEqual(resolve_value(42, {}), 42)

    def test_returns_string_without_token_unchanged(self) -> None:
        """Verify plain strings with no @ref token pass through unchanged."""

        self.assertEqual(resolve_value('hello', {}), 'hello')

    def test_resolves_whole_value_token(self) -> None:
        """Verify a string that is entirely one token is replaced with the raw resolved value."""

        result_map = {'step1': {'count': 3}}
        result = resolve_value('@ref{step1.count}', result_map)
        self.assertEqual(result, 3)
        self.assertIsInstance(result, int, 'Whole-value token should preserve the original type')

    def test_resolves_embedded_token_as_string(self) -> None:
        """Verify a token embedded in surrounding text is stringified and substituted."""

        result_map = {'step1': {'id': 99}}
        result = resolve_value('/items/@ref{step1.id}/detail', result_map)
        self.assertEqual(result, '/items/99/detail')

    def test_resolves_multiple_embedded_tokens(self) -> None:
        """Verify multiple tokens within a single string are all substituted."""

        result_map = {'a': {'x': 'foo'}, 'b': {'y': 'bar'}}
        result = resolve_value('@ref{a.x}-@ref{b.y}', result_map)
        self.assertEqual(result, 'foo-bar')

    def test_returns_list_unchanged(self) -> None:
        """Verify list values pass through without modification."""

        self.assertEqual(resolve_value([1, 2], {}), [1, 2])

    def test_raises_on_unresolvable_embedded_token(self) -> None:
        """Verify an embedded token referencing an unknown alias raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('/items/@ref{ghost.id}/', {})
