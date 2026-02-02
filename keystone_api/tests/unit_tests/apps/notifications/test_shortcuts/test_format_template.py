"""Unit tests for the `format_template` function."""

from django.test import TestCase
from jinja2 import Environment, StrictUndefined, Template, UndefinedError

from apps.notifications.shortcuts import format_template


class HtmlOutputTest(TestCase):
    """Tests for HTML output from format_template."""

    def test_interpolates_jinja_variables(self) -> None:
        """Verify Jinja2 variables are interpolated in HTML output."""

        template = Template("<h1>Hello {{ name }}</h1>")
        html, _ = format_template(template, {"name": "Alice"})

        self.assertEqual("<h1>Hello Alice</h1>", html)

    def test_preserves_html_entities(self) -> None:
        """Verify HTML entities are preserved in HTML output."""

        template = Template("<p>Use &lt;code&gt; for code and &amp; for ampersand.</p>")
        html, _ = format_template(template, {})

        self.assertIn("&lt;code&gt;", html)
        self.assertIn("&amp;", html)


class PlainTextOutput(TestCase):
    """Tests for plain text output from format_template."""

    def test_strips_html_tags(self) -> None:
        """Verify HTML tags are removed from plain text output."""

        template = Template("<p>This is <strong>bold</strong> text.</p>")
        _, text = format_template(template, {})

        self.assertNotIn("<p>", text)
        self.assertNotIn("<strong>", text)
        self.assertIn("This is bold text.", text)

    def test_decodes_html_entities(self) -> None:
        """Verify HTML entities are decoded in plain text output."""

        template = Template("<p>Use &lt;code&gt; for code and &amp; for ampersand.</p>")
        _, text = format_template(template, {})

        self.assertIn("<code>", text)
        self.assertIn("&", text)

    def test_br_tags_become_newlines(self) -> None:
        """Verify `br` tags are converted to newlines in plain text output."""

        template = Template("Line one<br>Line two<br>Line three")
        _, text = format_template(template, {})

        self.assertIn("Line one  \nLine two  \nLine three", text)

    def test_paragraph_tags_create_separation(self) -> None:
        """Verify paragraph tags create visual separation in plain text output."""

        template = Template("<p>First paragraph.</p><p>Second paragraph.</p>")
        _, text = format_template(template, {})

        self.assertIn("First paragraph.", text)
        self.assertIn("Second paragraph.", text)
        self.assertNotIn("First paragraph.Second paragraph.", text)

    def test_heading_content_preserved(self) -> None:
        """Verify heading tag content is preserved in plain text output."""

        template = Template("<h1>Main Title</h1><h2>Subtitle</h2>")
        _, text = format_template(template, {})

        self.assertIn("Main Title", text)
        self.assertIn("Subtitle", text)

    def test_list_item_content_preserved(self) -> None:
        """Verify list item content is preserved in plain text output."""

        template = Template("<ul><li>Item one</li><li>Item two</li></ul>")
        _, text = format_template(template, {})

        self.assertIn("Item one", text)
        self.assertIn("Item two", text)

    def test_link_text_preserved(self) -> None:
        """Verify link text is preserved in plain text output."""

        template = Template('<p>Visit <a href="https://example.com">our website</a> for info.</p>')
        _, text = format_template(template, {})

        self.assertIn("our website", text)
        self.assertIn("Visit", text)
        self.assertIn("for info.", text)

    def test_table_content_preserved(self) -> None:
        """Verify table cell content is preserved in plain text output."""

        template = Template("<table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>")
        _, text = format_template(template, {})

        self.assertIn("Cell 1", text)
        self.assertIn("Cell 2", text)

    def test_whitespace_normalized(self) -> None:
        """Verify consecutive whitespace is collapsed in plain text output."""

        template = Template("<p>   Hello    world.   </p>")
        _, text = format_template(template, {})

        self.assertNotIn("   ", text)
        self.assertIn("Hello", text)
        self.assertIn("world.", text)

    def test_nested_tag_content_preserved(self) -> None:
        """Verify content within nested tags is preserved in plain text output."""

        template = Template("<p>This is <strong>bold and <em>italic</em></strong> text.</p>")
        _, text = format_template(template, {})

        self.assertIn("bold and italic", text)


class TemplateContextHandling(TestCase):
    """Tests for template context handling in format_template."""

    def test_interpolates_context_variables(self) -> None:
        """Verify context variables are interpolated in output."""

        template = Template("Welcome, {{ user }}!")
        html, text = format_template(template, {"user": "Bob"})

        self.assertEqual("Welcome, Bob!", html)
        self.assertIn("Welcome, Bob!", text)

    def test_ignores_extra_context_variables(self) -> None:
        """Verify context variables not referenced in template do not affect output."""

        template = Template("Hello, {{ name }}!")
        context = {"name": "Alice", "unused": "ignored"}
        html, text = format_template(template, context)

        self.assertEqual("Hello, Alice!", html)
        self.assertNotIn("ignored", html)
        self.assertNotIn("ignored", text)

    def test_raises_error_for_missing_variable_in_strict_mode(self) -> None:
        """Verify UndefinedError is raised when StrictUndefined template is missing context variables."""

        env = Environment(undefined=StrictUndefined, autoescape=True)
        template = env.from_string("Hello {{ name }}")

        with self.assertRaises(UndefinedError):
            format_template(template, {})


class TemplateValidation(TestCase):
    """Tests for input validation in format_template."""

    def test_empty_template_raises_error(self) -> None:
        """Verify RuntimeError is raised when rendered template is empty."""

        with self.assertRaises(RuntimeError):
            format_template(Template(""), {})

    def test_whitespace_only_template_raises_error(self) -> None:
        """Verify RuntimeError is raised when rendered template contains only whitespace."""

        with self.assertRaises(RuntimeError):
            format_template(Template("   \n\t  "), {})
