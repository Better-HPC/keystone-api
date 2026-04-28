"""Unit tests for the `lookup_alias` function."""

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import lookup_alias


class LookupAliasFunction(TestCase):
    """Test the fetching of aliases from a results dictionary."""

    def test_resolves_known_alias(self) -> None:
        """Verify a known alias and valid dotpath return the expected value."""

        result_map = {'step1': {'id': 7}}
        result = lookup_alias('step1', 'id', '@ref{step1.id}', result_map)
        self.assertEqual(result, 7)

    def test_resolves_nested_dotpath(self) -> None:
        """Verify a multi-segment dotpath under an alias is traversed."""

        result_map = {'step1': {'user': {'name': 'Bob'}}}
        result = lookup_alias('step1', 'user.name', '@ref{step1.user.name}', result_map)
        self.assertEqual(result, 'Bob')

    def test_raises_on_unknown_alias(self) -> None:
        """Verify an alias absent from result_map raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            lookup_alias('missing', 'id', '@ref{missing.id}', {})

    def test_raises_when_dotpath_invalid_for_alias(self) -> None:
        """Verify a bad dotpath into a known alias raises `ReferenceResolutionError`."""

        result_map = {'step1': {'id': 1}}
        with self.assertRaises(ReferenceResolutionError):
            lookup_alias('step1', 'nonexistent', '@ref{step1.nonexistent}', result_map)

    def test_unknown_alias_error_includes_token(self) -> None:
        """Verify the error message for an unknown alias includes the original token."""

        token = '@ref{ghost.id}'
        with self.assertRaises(ReferenceResolutionError) as context:
            lookup_alias('ghost', 'id', token, {})

        self.assertIn(token, str(context.exception), 'Original token should appear in error message')