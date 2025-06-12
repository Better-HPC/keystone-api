"""Unit tests for the `get_template` function."""

import tempfile
from pathlib import Path

from django.test import override_settings, TestCase
from jinja2 import Template

from apps.notifications.shortcuts import get_template


class GetTemplateMethod(TestCase):
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

    def test_returns_custom_template_when_present(self) -> None:
        """Verify the custom template takes precedence over the default template."""

        custom_template_path = Path(self.custom_dir.name) / self.template_name
        custom_template_path.write_text(self.custom_template_content)

        default_template_path = Path(self.default_dir.name) / self.template_name
        default_template_path.write_text(self.default_template_content)

        with override_settings(EMAIL_TEMPLATE_DIR=Path(self.custom_dir.name)):
            tpl = get_template(self.template_name)

        self.assertIsInstance(tpl, Template)
        self.assertEqual(tpl.render(), self.custom_template_content)

    def test_falls_back_to_default_template_when_custom_not_found(self) -> None:
        """Verify the default template is returned when a custom template is not found."""

        default_template_path = Path(self.default_dir.name) / self.template_name
        default_template_path.write_text(self.default_template_content)

        with override_settings(EMAIL_TEMPLATE_DIR=Path(self.custom_dir.name)):
            tpl = get_template(self.template_name)

        self.assertIsInstance(tpl, Template)
        self.assertEqual(tpl.render(), self.default_template_content)

    def test_raises_error_if_no_template_exists(self) -> None:
        """Verify an error is raised if no template exists."""

        with self.assertRaises(FileNotFoundError):
            get_template(self.template_name)
