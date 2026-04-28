"""Unit tests for the `traverse_dotpath` function."""

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import traverse_dotpath


class TraverseDotpathFunction(TestCase):
    """Test the traversal of nested data structures using a dot-separated path."""

    def test_resolves_top_level_dict_key(self) -> None:
        """Verify a single-segment path returns the matching dict value."""

        result = traverse_dotpath({'id': 42}, 'id', '@ref{step.id}')
        self.assertEqual(result, 42)

    def test_resolves_nested_dict_path(self) -> None:
        """Verify a multi-segment dotpath walks nested dicts correctly."""

        data = {'user': {'name': 'Alice'}}
        result = traverse_dotpath(data, 'user.name', '@ref{step.user.name}')
        self.assertEqual(result, 'Alice')

    def test_resolves_list_index(self) -> None:
        """Verify an integer segment indexes into a list."""

        data = {'results': [{'id': 1}, {'id': 2}]}
        result = traverse_dotpath(data, 'results.1.id', '@ref{step.results.1.id}')
        self.assertEqual(result, 2)

    def test_resolves_mixed_dict_and_list_path(self) -> None:
        """Verify a dotpath alternating between dicts and lists resolves correctly."""

        data = {'items': [{'tags': ['a', 'b', 'c']}]}
        result = traverse_dotpath(data, 'items.0.tags.2', '@ref{step.items.0.tags.2}')
        self.assertEqual(result, 'c')

    def test_resolves_to_nested_container(self) -> None:
        """Verify a dotpath ending at a nested container returns that container."""

        data = {'user': {'name': 'Alice', 'age': 30}}
        result = traverse_dotpath(data, 'user', '@ref{step.user}')
        self.assertEqual(result, {'name': 'Alice', 'age': 30})

    def test_raises_on_missing_dict_key(self) -> None:
        """Verify a missing dict key raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            traverse_dotpath({'a': 1}, 'b', '@ref{step.b}')

    def test_raises_on_invalid_list_index(self) -> None:
        """Verify a non-integer list segment raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            traverse_dotpath([1, 2, 3], 'x', '@ref{step.x}')

    def test_raises_on_out_of_range_list_index(self) -> None:
        """Verify an out-of-range list index raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            traverse_dotpath([1, 2], '5', '@ref{step.5}')

    def test_raises_when_traversing_into_scalar(self) -> None:
        """Verify attempting to descend into a scalar raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            traverse_dotpath({'val': 99}, 'val.nested', '@ref{step.val.nested}')

    def test_error_message_includes_token(self) -> None:
        """Verify the raised error preserves the original token for diagnostic context."""

        token = '@ref{step.missing}'
        with self.assertRaises(ReferenceResolutionError) as context:
            traverse_dotpath({'a': 1}, 'missing', token)

        self.assertIn(token, str(context.exception), 'Original token should appear in error message')