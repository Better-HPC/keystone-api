"""Unit tests for the `EmlFileBasedEmailBackend` class."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings, SimpleTestCase

from plugins.email import EmlFileBasedEmailBackend


class GenerateFilePathMethod(SimpleTestCase):
    """Tests file name generation by the `generate_file_path` method."""

    def setUp(self) -> None:
        """Create a temporary directory for email output."""

        self._tempdir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self._tempdir.name)

        with override_settings(EMAIL_FILE_PATH=self.test_dir):
            self.backend = EmlFileBasedEmailBackend()

    def tearDown(self) -> None:
        """Clean up temporary files."""

        self._tempdir.cleanup()

    def test_file_path_with_subject(self) -> None:
        """Verify filenames are based on the slugified email subject."""

        message = Mock(subject="Test Subject Line")
        path = self.backend.generate_file_path(message)

        expected_filename = self.test_dir / "test-subject-line.eml"
        self.assertEqual(expected_filename, path)

    def test_file_path_with_empty_subject(self) -> None:
        """Verify filenames default to the current timestamp when there is no email subject."""

        message = Mock(subject="")
        mock_now = datetime(2024, 1, 1, 12, 0, 0)

        with patch("plugins.email.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            path = self.backend.generate_file_path(message)

        expected_filename = self.test_dir / f"{mock_now.timestamp()}.eml"
        self.assertEqual(path, expected_filename)

    def test_file_path_with_invalid_slug(self) -> None:
        """Verify filenames default to the current timestamp when the subject is not sluggable."""

        message = Mock(subject="!@#$%^&*()")
        mock_now = datetime(2024, 1, 1, 12, 0, 0)

        with patch("plugins.email.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            path = self.backend.generate_file_path(message)

        expected_filename = self.test_dir / f"{mock_now.timestamp()}.eml"
        self.assertEqual(path, expected_filename)

    def test_no_output_path_configured(self):
        """Verify an error is raised during init if an output path is not configured."""

        with override_settings(EMAIL_FILE_PATH=None):
            with self.assertRaises(ImproperlyConfigured):
                EmlFileBasedEmailBackend()

    def test_output_path_does_not_exist(self) -> None:
        """Verify an error is raised during init if the output path does not exist."""

        fake_path = Path("/tmp/nonexistent_test_emails")
        with override_settings(EMAIL_FILE_PATH=fake_path):
            with self.assertRaises(RuntimeError):
                EmlFileBasedEmailBackend()
