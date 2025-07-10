"""Unit tests for the `format_template` function."""

from django.test import TestCase
from jinja2 import Environment, StrictUndefined, Template, UndefinedError

from apps.notifications.shortcuts import format_template


class FormatTemplateMethod(TestCase):
    """Test the formatting of notification templates."""

    def test_renders_html_and_plain_text(self) -> None:
        """Verify templates are properly formatted and returned in HTML and PlainText."""

        template_str = "<h1>Hello {{ name }}</h1><p>Welcome to the site.</p><br>Thanks!"
        context = {"name": "Alice"}
        template = Template(template_str)

        html, text = format_template(template, context)

        expected_html = "<h1>Hello Alice</h1><p>Welcome to the site.</p><br>Thanks!"
        expected_text = "Hello Alice\n\nWelcome to the site.\nThanks!"

        self.assertEqual(expected_html, html)
        self.assertEqual(expected_text, text)

    def test_template_with_special_chars(self) -> None:
        """Verify special characters are properly fomratted in HTML and plain text."""

        template = Template("<p>Use &lt;code&gt; tags for code.</p>")
        html, text = format_template(template, {})

        expected_html = "<p>Use &lt;code&gt; tags for code.</p>"
        expected_text = "Use <code> tags for code."

        self.assertEqual(expected_html, html)
        self.assertEqual(expected_text, text)

    def test_newline_structure_preserved_in_plain_text(self) -> None:
        """Verify line breaks and paragraph structure are preserved in plain text."""

        template = Template("<p>Line one.</p><p>Line two.</p><p>Line<br>three.</p>")
        html, text = format_template(template, {})

        expected_html = "<p>Line one.</p><p>Line two.</p><p>Line<br>three.</p>"
        expected_text = "Line one.\n\nLine two.\n\nLine\nthree."

        self.assertEqual(expected_html, html)
        self.assertEqual(expected_text, text)

    def test_whitespace_normalization(self) -> None:
        """Verify excessive whitespace is normalized in plain text."""

        template = Template("<p>   Hello    world. </p>")
        html, text = format_template(template, {})

        expected_text = "Hello world."
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

    def test_respects_strict_mode(self) -> None:
        """Verify an error is raised when rendering a StrictUndefined template with missing variables."""

        env = Environment(undefined=StrictUndefined, autoescape=True)
        template = env.from_string("Hello {{ name }}")
        with self.assertRaises(UndefinedError):
            format_template(template, {})
