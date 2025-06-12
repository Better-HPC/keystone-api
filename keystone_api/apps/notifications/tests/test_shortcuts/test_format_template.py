"""Unit tests for the `format_template` function."""

from django.test import TestCase
from jinja2 import Template, UndefinedError

from apps.notifications.shortcuts import format_template


class FormatTemplateMethod(TestCase):
    """Test the formatting of notification templates."""

    def test_renders_html_and_plain_text(self) -> None:
        """Verify templates are properly formatted and returned in HTML and PlainText."""

        template_str = "<h1>Hello {{ name }}</h1>\n<p>Welcome to the site.</p>"
        context = {"name": "Alice"}
        template = Template(template_str)

        html, text = format_template(template, context)

        expected_html = "<h1>Hello Alice</h1>\n<p>Welcome to the site.</p>"
        expected_text = "Hello Alice\nWelcome to the site."

        self.assertEqual(expected_html, html)
        self.assertEqual(expected_text, text)

    def test_template_with_special_chars(self) -> None:
        """Verify special characters are respected."""

        template = Template("<p>Use &lt;code&gt; tags for code.</p>")
        html, text = format_template(template, {})

        expected_html = "<p>Use &lt;code&gt; tags for code.</p>"
        expected_text = "Use <code> tags for code."

        self.assertEqual(expected_html, html)
        self.assertEqual(expected_text, text)

    def test_extra_context_variable_is_ignored(self) -> None:
        """Verify extra context variables are ignored."""

        template = Template("Welcome, {{ user }}!")
        context = {
            "user": "Bob",
            "irrelevant": "should be ignored"
        }

        html, text = format_template(template, context)
        self.assertEqual("Welcome, Bob!", html)
        self.assertEqual("Welcome, Bob!", text)

    def test_empty_template_raises_error(self) -> None:
        """Verify an error is raised for empty templates."""

        with self.assertRaises(RuntimeError):
            format_template(Template(""), {})

    def test_missing_context_variable_raises_error(self) -> None:
        """Verify an error is raised when a template is missing context variables."""

        template = Template("Hello {{ name }}")
        context = {}  # Missing 'name' field

        with self.assertRaises(UndefinedError):
            format_template(template, context)
