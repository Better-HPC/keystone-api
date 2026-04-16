"""Unit tests for the `JobSerializer` class."""

from django.test import TestCase

from apps.batch.serializers import JobSerializer


class ValidateActionsMethod(TestCase):
    """Test validation of the `JobSerializer.actions` field."""

    def _valid_step(self, ref: str = '') -> dict:
        """Return a minimal valid step descriptor."""

        return {'method': 'GET', 'path': '/items/', 'ref': ref}

    def test_unique_refs_pass_validation(self) -> None:
        """Verify a list of steps with distinct ref aliases passes validation."""

        serializer = JobSerializer(data={
            'actions': [self._valid_step('a'), self._valid_step('b')],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_duplicate_refs_raise_validation_error(self) -> None:
        """Verify duplicate ref aliases within actions fail validation."""

        serializer = JobSerializer(data={
            'actions': [self._valid_step('same'), self._valid_step('same')],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('actions', serializer.errors)

    def test_multiple_steps_with_empty_refs_pass_validation(self) -> None:
        """Verify multiple steps all omitting ref do not trigger the uniqueness check."""

        serializer = JobSerializer(data={
            'actions': [self._valid_step(), self._valid_step(), self._valid_step()],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_actions_list_fails_validation(self) -> None:
        """Verify an empty actions list fails validation."""

        serializer = JobSerializer(data={'actions': []})
        self.assertFalse(serializer.is_valid())
        self.assertIn('actions', serializer.errors)

    def test_mixed_refs_and_empty_strings_deduplicated_correctly(self) -> None:
        """Verify steps mixing named and empty refs passes validation."""

        serializer = JobSerializer(data={
            'actions': [
                self._valid_step('alpha'),
                self._valid_step(''),
                self._valid_step(''),
                self._valid_step('beta'),
            ],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
