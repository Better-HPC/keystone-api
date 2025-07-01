"""Unit tests for the `get_template` function."""

import tempfile
from pathlib import Path

from django.test import override_settings, TestCase
from jinja2 import StrictUndefined, Template

from apps.notifications.shortcuts import get_template


class TemplateResolution(TestCase):
    """Test fetching notification templates via the `get_template` function."""

    def setUp(self) -> None:
        """Define test fixtures and create temporary directories."""

        # Define values for a custom email template
        self.template_name = "test_template.html"
        self.custom_template_content = "Custom Template Content"
        self.default_template_content = "Default Template Content"

        # Create a temporary directories for storing test files
        self.custom_dir = tempfile.TemporaryDirectory()
        self.default_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Clean up temporary directories."""

        self.custom_dir.cleanup()
        self.default_dir.cleanup()

    def _prepare_template(self, directory: tempfile.TemporaryDirectory, content: str, chmod: int = 0o440) -> None:
        """Helper function for creating a template file in the given directory.

        Args:
            directory: The directory to create the template in.
            content: The content of the template.
            chmod: The permissions of the file in OCTAL format.
        """

        template_path = Path(directory.name) / self.template_name
        template_path.write_text(content)
        template_path.chmod(chmod)

    def test_returns_custom_template_when_present(self) -> None:
        """Verify the custom template takes precedence over the default template."""

        self._prepare_template(self.custom_dir, self.custom_template_content)
        self._prepare_template(self.default_dir, self.default_template_content)

        with override_settings(
            EMAIL_TEMPLATE_DIR=Path(self.custom_dir.name),
            EMAIL_DEFAULT_DIR=Path(self.default_dir.name),
        ):
            template = get_template(self.template_name)

        self.assertIsInstance(template, Template)
        self.assertEqual(self.custom_template_content, template.render())

    def test_falls_back_to_default_template_when_custom_not_found(self) -> None:
        """Verify the default template is returned when a custom template is not found."""

        self._prepare_template(self.default_dir, self.default_template_content)

        with override_settings(EMAIL_DEFAULT_DIR=Path(self.default_dir.name)):
            template = get_template(self.template_name)

        self.assertIsInstance(template, Template)
        self.assertEqual(self.default_template_content, template.render())

    def test_raises_error_if_no_template_exists(self) -> None:
        """Verify an error is raised if no template exists."""

        with self.assertRaises(FileNotFoundError):
            get_template(self.template_name)

    def test_strict_undefined_enabled(self) -> None:
        """Verify the returned template is configured to enforce StrictUndefined mode."""

        self._prepare_template(self.default_dir, self.default_template_content)

        with override_settings(EMAIL_DEFAULT_DIR=Path(self.default_dir.name)):
            template = get_template(self.template_name)

        self.assertIs(template.environment.undefined, StrictUndefined)

    def test_file_permissions_restricted(self) -> None:
        """Verify an error is raised when loading templates with `O+W` permissions."""

        # Create a template with world-writable permissions
        self._prepare_template(self.default_dir, self.default_template_content, chmod=0o446)

        with (
            override_settings(EMAIL_DEFAULT_DIR=Path(self.default_dir.name)),
            self.assertRaisesRegex(PermissionError, "Template file has insecure file permissions")
        ):
            get_template(self.template_name)
