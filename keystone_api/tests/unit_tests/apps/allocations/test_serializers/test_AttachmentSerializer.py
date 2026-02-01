"""Unit tests for the `AttachmentSerializer` class."""

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, TestCase
from rest_framework.exceptions import ValidationError

from apps.allocations.serializers import AttachmentSerializer

KB = 1024  # One KB in bytes


@override_settings(MAX_FILE_SIZE=KB)
class ValidateFileMethod(TestCase):
    """Test the validation of file upload data."""

    def test_under_size_limit(self) -> None:
        """Verify files below the size limit pass validation."""

        max_size = settings.MAX_FILE_SIZE
        file = SimpleUploadedFile("file.txt", b"x" * (max_size - 1))  # 1 KB

        result = AttachmentSerializer.validate_file(file)
        self.assertEqual(result, file)

    def test_equals_size_limit(self) -> None:
        """Verify files equal to the size limit pass validation."""

        max_size = settings.MAX_FILE_SIZE
        file = SimpleUploadedFile("large.txt", b"x" * max_size)

        result = AttachmentSerializer.validate_file(file)
        self.assertEqual(result, file)

    def test_exceeds_size_limit(self) -> None:
        """Verify files above the size limit fail validation."""

        max_size = settings.MAX_FILE_SIZE
        file = SimpleUploadedFile("large.txt", b"x" * (max_size + 1))

        with self.assertRaisesRegex(ValidationError, "File size should not exceed"):
            AttachmentSerializer.validate_file(file)

    def test_allowed_mime_type(self) -> None:
        """Verify a file with an allowed MIME type passes validation."""

        file = SimpleUploadedFile("test.txt", b"sample content")
        result = AttachmentSerializer.validate_file(file)
        self.assertEqual(result, file)

    def test_disallowed_mime_type(self) -> None:
        """Verify a file with a disallowed MIME type fails validation."""

        file = SimpleUploadedFile("text.exe", b"GIF87a...")
        with self.assertRaisesRegex(ValidationError, "File type .* is not allowed"):
            AttachmentSerializer.validate_file(file)
