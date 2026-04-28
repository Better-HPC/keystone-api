"""Unit tests for the `resolve_value` function."""

from unittest.mock import Mock

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import resolve_value


class ResolveValueFunction(TestCase):
    """Test the formatting of values containing `@ref` and `@file` placeholders."""

    def test_returns_string_without_token_unchanged(self) -> None:
        """Verify plain strings with no @ref token pass through unchanged."""

        self.assertEqual(resolve_value('hello', {}), 'hello')

    def test_resolves_whole_value_int_token(self) -> None:
        """Verify a whole-value token resolving to an `int` type returns the integer directly."""

        result_map = {'step1': {'count': 3}}
        result = resolve_value('@ref{step1.count}', result_map)

        self.assertEqual(result, 3)
        self.assertIsInstance(result, int, 'Whole-value token should preserve the original type')

    def test_resolves_whole_value_token_to_list(self) -> None:
        """Verify a whole-value token resolving to a `list` type returns the list directly."""

        result_map = {'step1': {'tags': ['a', 'b']}}
        result = resolve_value('@ref{step1.tags}', result_map)

        self.assertEqual(result, ['a', 'b'])
        self.assertIsInstance(result, list, 'Whole-value token should preserve list type')

    def test_resolves_whole_value_bool_token(self) -> None:
        """Verify a whole-value token resolving to a `bool` type returns the boolean directly."""

        result_map = {'step1': {'flag': False}}
        result = resolve_value('@ref{step1.flag}', result_map)
        self.assertIs(result, False)

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

    def test_resolves_whole_value_file_token(self) -> None:
        """Verify a whole-value @file token returns the matching file object directly."""

        upload = Mock()
        files = {'avatar': upload}
        result = resolve_value('@file{avatar}', {}, files=files)
        self.assertIs(result, upload, 'File token should return the uploaded object directly')

    def test_raises_on_unresolvable_token(self) -> None:
        """Verify a token with no matching value raises a `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('/items/@ref{ghost.id}/', {})

    def test_raises_on_missing_file_part(self) -> None:
        """Verify a @file token with no matching file raises a `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('@file{missing}', {}, files={})

    def test_raises_when_files_dict_is_none(self) -> None:
        """Verify a @file token raises when no files dict is supplied."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('@file{avatar}', {}, files=None)

    def test_raises_on_invalid_ref_label_characters(self) -> None:
        """Verify a @ref token containing disallowed characters raises a `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('@ref{bad-name!.count}', {'bad-name!': {'count': 3}}, files=None)

    def test_raises_on_invalid_file_label_characters(self) -> None:
        """Verify a @file token containing disallowed characters raises a `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            resolve_value('@file{bad-name!}', {}, files={'bad-name!': Mock()})
