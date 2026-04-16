"""Unit tests for the `lookup` function."""

from django.test import TestCase

from apps.batch.exceptions import ReferenceResolutionError
from apps.batch.shortcuts import lookup_alias


class LookupMethod(TestCase):
    """Test the fetching of aliases from a results dictionary."""

    def test_resolves_known_alias(self) -> None:
        """Verify a known alias and valid dotpath return the expected value."""

        result_map = {'step1': {'id': 7}}
        result = lookup_alias('step1', 'id', '@ref{step1.id}', result_map)
        self.assertEqual(result, 7)

    def test_raises_on_unknown_alias(self) -> None:
        """Verify an alias absent from result_map raises `ReferenceResolutionError`."""

        with self.assertRaises(ReferenceResolutionError):
            lookup_alias('missing', 'id', '@ref{missing.id}', {})

    def test_raises_when_dotpath_invalid_for_alias(self) -> None:
        """Verify a bad dotpath into a known alias raises `ReferenceResolutionError`."""

        result_map = {'step1': {'id': 1}}
        with self.assertRaises(ReferenceResolutionError):
            lookup_alias('step1', 'nonexistent', '@ref{step1.nonexistent}', result_map)
