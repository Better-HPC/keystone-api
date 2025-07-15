"""Unit tests for the `EmlFileEmailBackend` class."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.test import override_settings, TestCase

from plugins.email import EmlFileEmailBackend


class GenerateFilePathMethod(TestCase):
    """Test file name generation by the `generate_file_path` method."""

    def setUp(self) -> None:
        """Create a temporary directory for file outputs."""

        self._tempdir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self._tempdir.name)

        with override_settings(EMAIL_FILE_PATH=self.test_dir):
            self.backend = EmlFileEmailBackend()

    def tearDown(self) -> None:
        """Clean up temporary files."""

        self._tempdir.cleanup()

    def test_file_path_with_subject(self) -> None:
        """Verify filenames are based on the slugified message subject."""

        message = Mock(subject="Test Subject Line")
        path = self.backend.generate_file_path(message)

        expected_filename = self.test_dir / "test-subject-line.eml"
        self.assertEqual(expected_filename, path)

    def test_file_path_with_empty_subject(self) -> None:
        """Verify filenames default to the current timestamp when there is no message subject."""

        message = Mock(subject="")
        mock_now = datetime(2024, 1, 1, 12, 0, 0)

        with patch("plugins.email.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            path = self.backend.generate_file_path(message)

        expected_filename = self.test_dir / f"{mock_now.timestamp()}.eml"
        self.assertEqual(path, expected_filename)

    def test_file_path_with_invalid_slug(self) -> None:
        """Verify filenames default to the current timestamp when the message subject is not sluggable."""

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
                EmlFileEmailBackend()

    def test_output_path_does_not_exist(self) -> None:
        """Verify an error is raised during init if the output path does not exist."""

        fake_path = Path("/tmp/nonexistent_test_emails")
        with override_settings(EMAIL_FILE_PATH=fake_path):
            with self.assertRaises(RuntimeError):
                EmlFileEmailBackend()


class SendMessagesMethod(TestCase):
    """Test sending multiple messages via the `send_messages` method."""

    def setUp(self) -> None:
        """Set up a temporary output directory for the backend."""

        self._tempdir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self._tempdir.name)
        with override_settings(EMAIL_FILE_PATH=self.test_dir):
            self.backend = EmlFileEmailBackend()

    def tearDown(self) -> None:
        """Clean up temporary files."""

        self._tempdir.cleanup()

    def test_calls_write_message_for_each_email(self) -> None:
        """Verify the `write_message` method is called for each message."""

        messages = [
            EmailMessage(subject="one", body="Body 1", from_email="a@x.com", to=["b@x.com"]),
            EmailMessage(subject="two", body="Body 2", from_email="a@x.com", to=["c@x.com"]),
            EmailMessage(subject="three", body="Body 3", from_email="a@x.com", to=["d@x.com"]),
        ]

        with patch.object(self.backend, "write_message") as mock_write:
            self.backend.send_messages(messages)

        self.assertEqual(len(messages), mock_write.call_count)
        mock_write.assert_any_call(messages[0])
        mock_write.assert_any_call(messages[1])
        mock_write.assert_any_call(messages[2])


class WriteMessageMethod(TestCase):
    """Test writing messages to disk via the `write_message` method."""

    def setUp(self) -> None:
        """Create a temporary directory for file outputs."""

        self._tempdir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self._tempdir.name)

        with override_settings(EMAIL_FILE_PATH=self.test_dir):
            self.backend = EmlFileEmailBackend()

    def tearDown(self) -> None:
        """Clean up temporary files."""

        self._tempdir.cleanup()

    def test_writes_correct_content(self) -> None:
        """Verify message content is written to the output file."""

        target_file = self.test_dir / "test-output.eml"
        email = EmailMessage(subject="test subject", body="This is the body of the email.")
        with patch.object(self.backend, "generate_file_path", return_value=target_file):
            self.backend.write_message(email)

        with open(target_file) as f:
            content = f.read()

        self.assertIn("This is the body of the email.", content)
        self.assertIn("Subject: test subject", content)

    def test_overwrites_existing_file(self) -> None:
        """Verify existing files are overwritten."""

        # Populate the destination file with existing content
        target_file = self.test_dir / "overwrite-test.eml"
        with open(target_file, "w") as f:
            f.write("Old content that should be replaced.")

        # Execute the email backend
        email = EmailMessage(subject="overwrite test", body="New content.")
        with patch.object(self.backend, "generate_file_path", return_value=target_file):
            self.backend.write_message(email)

        with open(target_file) as f:
            content = f.read()

        # Verify the file content was overwritten
        self.assertIn("New content.", content)
        self.assertNotIn("Old content that should be replaced.", content)
