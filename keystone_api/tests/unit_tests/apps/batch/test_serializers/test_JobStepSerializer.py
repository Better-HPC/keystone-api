"""Unit tests for the `JobStepSerializer` class."""

from django.test import TestCase

from apps.batch.serializers import JobStepSerializer


class ValidateRefMethod(TestCase):
    """Test validation of the `JobStepSerializer.ref` field."""

    def _make_serializer(self, data: dict) -> JobStepSerializer:
        """Return a partially bound serializer for validate_ref testing."""

        return JobStepSerializer(data=data)

    def test_valid_alphanumeric_ref_passes(self) -> None:
        """Verify an alphanumeric ref alias is accepted without error."""

        serializer = self._make_serializer({
            'method': 'GET',
            'path': '/items/',
            'ref': 'step1',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_ref_with_underscore_passes(self) -> None:
        """Verify a ref alias containing underscores is accepted."""

        serializer = self._make_serializer({
            'method': 'GET',
            'path': '/items/',
            'ref': 'my_step',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_ref_passes(self) -> None:
        """Verify an empty string ref is accepted."""

        serializer = self._make_serializer({'method': 'GET', 'path': '/items/', 'ref': ''})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_ref_with_hyphen_raises_validation_error(self) -> None:
        """Verify a ref alias containing a hyphen fails validation."""

        serializer = self._make_serializer({
            'method': 'GET',
            'path': '/items/',
            'ref': 'bad-ref',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('ref', serializer.errors)

    def test_ref_with_space_raises_validation_error(self) -> None:
        """Verify a ref alias containing a space fails validation."""

        serializer = self._make_serializer({
            'method': 'GET',
            'path': '/items/',
            'ref': 'bad ref',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('ref', serializer.errors)

    def test_ref_with_dot_raises_validation_error(self) -> None:
        """Verify a ref alias containing a dot fails validation."""

        serializer = self._make_serializer({
            'method': 'GET',
            'path': '/items/',
            'ref': 'step.1',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('ref', serializer.errors)

    def test_omitted_ref_defaults_to_empty_string(self) -> None:
        """Verify omitting ref defaults to an empty string and passes validation."""

        serializer = self._make_serializer({'method': 'GET', 'path': '/items/'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['ref'], '')
