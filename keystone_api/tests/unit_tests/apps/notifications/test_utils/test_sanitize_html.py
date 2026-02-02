"""Tests for HTML sanitization utilities."""

from django.test import TestCase

from apps.notifications.utils import sanitize_html


class SanitizeHtmlJavaScriptRemovalTest(TestCase):
    """Tests for JavaScript removal from HTML."""

    def test_removes_script_tags(self) -> None:
        """Verify script tags and their contents are completely removed."""

        html = '<div>Hello</div><script>alert("xss")</script><p>World</p>'
        result = sanitize_html(html)
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert', result)
        self.assertIn('<div>Hello</div>', result)
        self.assertIn('<p>World</p>', result)

    def test_removes_script_tags_with_attributes(self) -> None:
        """Verify script tags with type and src attributes are removed."""

        html = '<script type="text/javascript" src="evil.js"></script>'
        result = sanitize_html(html)
        self.assertNotIn('<script', result)
        self.assertNotIn('evil.js', result)

    def test_removes_event_handlers(self) -> None:
        """Verify all on* event handler attributes are stripped regardless of name."""

        html = '<div onclick="alert(1)" onfoobar="alert(2)" onmade_up_event="alert(3)">Test</div>'
        result = sanitize_html(html)
        self.assertNotIn('onclick', result)
        self.assertNotIn('onfoobar', result)
        self.assertNotIn('onmade_up_event', result)
        self.assertNotIn('alert', result)

    def test_removes_event_handlers_case_insensitive(self) -> None:
        """Verify event handler removal is case-insensitive."""

        html = '<div OnClick="alert(1)" ONLOAD="alert(2)">Test</div>'
        result = sanitize_html(html)
        self.assertNotIn('alert', result)

    def test_removes_javascript_url_in_href(self) -> None:
        """Verify javascript: URLs are removed from href attributes."""

        html = '<a href="javascript:alert(\'xss\')">Click me</a>'
        result = sanitize_html(html)
        self.assertNotIn('javascript:', result)

    def test_removes_javascript_url_with_whitespace(self) -> None:
        """Verify javascript: URLs with leading whitespace are removed."""

        html = '<a href="  javascript:alert(\'xss\')">Click me</a>'
        result = sanitize_html(html)
        self.assertNotIn('javascript:', result)

    def test_removes_javascript_url_mixed_case(self) -> None:
        """Verify javascript: URL removal is case-insensitive."""

        html = '<a href="JaVaScRiPt:alert(\'xss\')">Click me</a>'
        result = sanitize_html(html)
        self.assertNotIn('javascript:', result.lower())


class SanitizeHtmlCssRemovalTest(TestCase):
    """Tests for dangerous CSS removal from HTML."""

    def test_removes_css_import(self) -> None:
        """Verify @import rules with url() syntax are removed from style tags."""

        html = '<style>@import url("https://evil.com/styles.css");</style>'
        result = sanitize_html(html)
        self.assertNotIn('@import', result)
        self.assertNotIn('evil.com', result)

    def test_removes_css_import_without_url(self) -> None:
        """Verify @import rules with string syntax are removed from style tags."""

        html = '<style>@import "https://evil.com/styles.css";</style>'
        result = sanitize_html(html)
        self.assertNotIn('@import', result)

    def test_removes_font_face(self) -> None:
        """Verify @font-face blocks are completely removed."""

        html = '<style>@font-face { font-family: Evil; src: url("https://evil.com/font.woff"); }</style>'
        result = sanitize_html(html)
        self.assertNotIn('@font-face', result)
        self.assertNotIn('evil.com', result)

    def test_removes_external_url_in_background(self) -> None:
        """Verify external URLs in background property are removed."""

        html = '<div style="background: url(https://evil.com/track.gif)">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('evil.com', result)

    def test_removes_external_url_in_background_image(self) -> None:
        """Verify external URLs in background-image property are removed."""

        html = '<div style="background-image: url(\'https://evil.com/track.gif\')">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('evil.com', result)

    def test_removes_protocol_relative_url(self) -> None:
        """Verify protocol-relative URLs (//) in styles are removed."""

        html = '<div style="background: url(//evil.com/track.gif)">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('evil.com', result)

    def test_preserves_data_uri_in_style(self) -> None:
        """Verify data: URIs in styles are preserved."""

        html = '<div style="background: url(data:image/png;base64,abc123)">Content</div>'
        result = sanitize_html(html)
        self.assertIn('data:image/png;base64,abc123', result)

    def test_removes_expression(self) -> None:
        """Verify IE expression() CSS hack is removed."""

        html = '<div style="width: expression(alert(\'xss\'))">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('expression', result)
        self.assertNotIn('alert', result)

    def test_removes_behavior(self) -> None:
        """Verify IE behavior: CSS property is removed."""

        html = '<div style="behavior: url(script.htc)">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('behavior', result)
        self.assertNotIn('script.htc', result)

    def test_removes_moz_binding(self) -> None:
        """Verify Firefox -moz-binding CSS property is removed."""

        html = '<div style="-moz-binding: url(script.xml#xss)">Content</div>'
        result = sanitize_html(html)
        self.assertNotIn('-moz-binding', result)
        self.assertNotIn('script.xml', result)

    def test_removes_external_url_in_style_tag(self) -> None:
        """Verify external URLs inside style tags are removed."""

        html = '<style>.evil { background: url(https://evil.com/track.gif); }</style>'
        result = sanitize_html(html)
        self.assertNotIn('evil.com', result)

    def test_preserves_safe_inline_styles(self) -> None:
        """Verify safe CSS properties are preserved in inline styles."""

        html = '<div style="color: red; font-size: 14px; margin: 10px;">Content</div>'
        result = sanitize_html(html)
        self.assertIn('color: red', result)
        self.assertIn('font-size: 14px', result)
        self.assertIn('margin: 10px', result)


class SanitizeHtmlTagWhitelistTest(TestCase):
    """Tests for HTML tag whitelist enforcement."""

    def test_allows_common_formatting_tags(self) -> None:
        """Verify common text formatting tags are preserved."""

        html = '<p><strong>Bold</strong> and <em>italic</em> and <u>underline</u></p>'
        result = sanitize_html(html)
        self.assertIn('<p>', result)
        self.assertIn('<strong>', result)
        self.assertIn('<em>', result)
        self.assertIn('<u>', result)

    def test_allows_heading_tags(self) -> None:
        """Verify heading tags h1-h3 are preserved."""

        html = '<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>'
        result = sanitize_html(html)
        self.assertIn('<h1>', result)
        self.assertIn('<h2>', result)
        self.assertIn('<h3>', result)

    def test_allows_list_tags(self) -> None:
        """Verify ordered and unordered list tags are preserved."""

        html = '<ul><li>Item 1</li><li>Item 2</li></ul><ol><li>First</li></ol>'
        result = sanitize_html(html)
        self.assertIn('<ul>', result)
        self.assertIn('<ol>', result)
        self.assertIn('<li>', result)

    def test_allows_table_tags(self) -> None:
        """Verify table structure tags are preserved."""

        html = '<table><thead><tr><th>Header</th></tr></thead><tbody><tr><td>Cell</td></tr></tbody></table>'
        result = sanitize_html(html)
        self.assertIn('<table>', result)
        self.assertIn('<thead>', result)
        self.assertIn('<tbody>', result)
        self.assertIn('<tr>', result)
        self.assertIn('<th>', result)
        self.assertIn('<td>', result)

    def test_allows_image_tags(self) -> None:
        """Verify img tags with src and alt attributes are preserved."""

        html = '<img src="https://example.com/image.jpg" alt="Example">'
        result = sanitize_html(html)
        self.assertIn('<img', result)
        self.assertIn('src="https://example.com/image.jpg"', result)
        self.assertIn('alt="Example"', result)

    def test_allows_anchor_tags(self) -> None:
        """Verify anchor tags with href are preserved."""

        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('<a', result)
        self.assertIn('href="https://example.com"', result)

    def test_allows_style_tags(self) -> None:
        """Verify style tags and their contents are preserved."""

        html = '<style>.class { color: red; }</style>'
        result = sanitize_html(html)
        self.assertIn('<style>', result)
        self.assertIn('.class { color: red; }', result)

    def test_removes_iframe_tags(self) -> None:
        """Verify iframe tags are removed."""

        html = '<iframe src="https://evil.com"></iframe>'
        result = sanitize_html(html)
        self.assertNotIn('<iframe', result)
        self.assertNotIn('evil.com', result)

    def test_removes_object_tags(self) -> None:
        """Verify object tags are removed."""

        html = '<object data="https://evil.com/flash.swf"></object>'
        result = sanitize_html(html)
        self.assertNotIn('<object', result)

    def test_removes_embed_tags(self) -> None:
        """Verify embed tags are removed."""

        html = '<embed src="https://evil.com/flash.swf">'
        result = sanitize_html(html)
        self.assertNotIn('<embed', result)

    def test_removes_form_tags(self) -> None:
        """Verify form and input tags are removed."""

        html = '<form action="https://evil.com"><input type="text"></form>'
        result = sanitize_html(html)
        self.assertNotIn('<form', result)
        self.assertNotIn('<input', result)


class SanitizeHtmlAttributeWhitelistTest(TestCase):
    """Tests for HTML attribute whitelist enforcement."""

    def test_allows_class_attribute(self) -> None:
        """Verify class attribute is preserved."""

        html = '<div class="container">Content</div>'
        result = sanitize_html(html)
        self.assertIn('class="container"', result)

    def test_allows_id_attribute(self) -> None:
        """Verify id attribute is preserved."""

        html = '<div id="main">Content</div>'
        result = sanitize_html(html)
        self.assertIn('id="main"', result)

    def test_allows_style_attribute(self) -> None:
        """Verify style attribute is preserved."""

        html = '<div style="color: blue;">Content</div>'
        result = sanitize_html(html)
        self.assertIn('style="color: blue;"', result)

    def test_allows_href_on_anchor(self) -> None:
        """Verify href and target attributes are preserved on anchors."""

        html = '<a href="https://example.com" target="_blank">Link</a>'
        result = sanitize_html(html)
        self.assertIn('href="https://example.com"', result)
        self.assertIn('target="_blank"', result)

    def test_allows_src_and_alt_on_image(self) -> None:
        """Verify src, alt, width, and height attributes are preserved on images."""

        html = '<img src="image.jpg" alt="Description" width="100" height="100">'
        result = sanitize_html(html)
        self.assertIn('src="image.jpg"', result)
        self.assertIn('alt="Description"', result)
        self.assertIn('width="100"', result)
        self.assertIn('height="100"', result)

    def test_allows_colspan_and_rowspan_on_td(self) -> None:
        """Verify colspan and rowspan attributes are preserved on table cells."""

        html = '<table><tr><td colspan="2" rowspan="3">Cell</td></tr></table>'
        result = sanitize_html(html)
        self.assertIn('colspan="2"', result)
        self.assertIn('rowspan="3"', result)

    def test_allows_aria_attributes(self) -> None:
        """Verify ARIA accessibility attributes are preserved."""

        html = '<div aria-label="Description" aria-hidden="true">Content</div>'
        result = sanitize_html(html)
        self.assertIn('aria-label="Description"', result)
        self.assertIn('aria-hidden="true"', result)

    def test_allows_data_value_attribute(self) -> None:
        """Verify value attribute is preserved on data elements."""

        html = '<data value="123">One hundred twenty-three</data>'
        result = sanitize_html(html)
        self.assertIn('value="123"', result)

    def test_adds_rel_noopener_to_links(self) -> None:
        """Verify rel="noopener noreferrer" is automatically added to links."""

        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('rel="noopener noreferrer"', result)


class SanitizeHtmlUrlSchemeTest(TestCase):
    """Tests for URL scheme enforcement."""

    def test_allows_http_urls(self) -> None:
        """Verify http:// URLs are allowed in href attributes."""

        html = '<a href="http://example.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('href="http://example.com"', result)

    def test_allows_https_urls(self) -> None:
        """Verify https:// URLs are allowed in href attributes."""

        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        self.assertIn('href="https://example.com"', result)

    def test_allows_mailto_urls(self) -> None:
        """Verify mailto: URLs are allowed in href attributes."""

        html = '<a href="mailto:test@example.com">Email</a>'
        result = sanitize_html(html)
        self.assertIn('href="mailto:test@example.com"', result)

    def test_removes_data_url_in_href(self) -> None:
        """Verify data: URLs are removed from href attributes."""

        html = '<a href="data:text/html,<script>alert(1)</script>">Link</a>'
        result = sanitize_html(html)
        self.assertNotIn('data:', result)

    def test_removes_vbscript_url(self) -> None:
        """Verify vbscript: URLs are removed from href attributes."""

        html = '<a href="vbscript:msgbox(1)">Link</a>'
        result = sanitize_html(html)
        self.assertNotIn('vbscript:', result)


class SanitizeHtmlEdgeCasesTest(TestCase):
    """Tests for edge cases and complex inputs."""

    def test_handles_empty_string(self) -> None:
        """Verify empty string input returns empty string."""

        result = sanitize_html('')
        self.assertEqual('', result)

    def test_handles_plain_text(self) -> None:
        """Verify plain text without HTML is returned unchanged."""

        html = 'Just plain text without any HTML'
        result = sanitize_html(html)
        self.assertEqual(html, result)

    def test_handles_nested_dangerous_content(self) -> None:
        """Verify dangerous content is removed even when deeply nested."""

        html = '<div><p><span onclick="alert(1)"><a href="javascript:void(0)">Link</a></span></p></div>'
        result = sanitize_html(html)
        self.assertNotIn('onclick', result)
        self.assertNotIn('javascript:', result)
        self.assertIn('<div>', result)
        self.assertIn('<p>', result)
        self.assertIn('<span>', result)

    def test_handles_multiple_style_tags(self) -> None:
        """Verify multiple style tags are each sanitized independently."""

        html = '<style>@import "evil.css";</style><style>.safe { color: red; }</style>'
        result = sanitize_html(html)
        self.assertNotIn('@import', result)
        self.assertIn('.safe { color: red; }', result)

    def test_handles_mixed_safe_and_unsafe_styles(self) -> None:
        """Verify safe styles are preserved while unsafe styles are removed."""

        html = '<div style="color: red; background: url(https://evil.com/x.gif); font-size: 12px;">Content</div>'
        result = sanitize_html(html)
        self.assertIn('color: red', result)
        self.assertIn('font-size: 12px', result)
        self.assertNotIn('evil.com', result)

    def test_preserves_html_entities(self) -> None:
        """Verify HTML entities are preserved and not decoded."""

        html = '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
        result = sanitize_html(html)
        self.assertIn('&lt;script&gt;', result)

    def test_handles_deeply_nested_elements(self) -> None:
        """Verify deeply nested elements are preserved."""

        html = '<div><div><div><div><p>Deep content</p></div></div></div></div>'
        result = sanitize_html(html)
        self.assertIn('Deep content', result)
        self.assertEqual(4, result.count('<div>'))

    def test_strips_html_comments(self) -> None:
        """Verify HTML comments are removed."""

        html = '<p>Before</p><!-- This is a comment --><p>After</p>'
        result = sanitize_html(html)
        self.assertNotIn('<!--', result)
        self.assertNotIn('comment', result)
        self.assertIn('<p>Before</p>', result)
        self.assertIn('<p>After</p>', result)

    def test_handles_invalid_html_structure(self) -> None:
        """Verify elements outside valid parent context (e.g., td without table) preserve content."""

        html = '<td colspan="2">Cell</td><li>Item</li><tr><th>Header</th></tr>'
        result = sanitize_html(html)
        self.assertIn('Cell', result)
        self.assertIn('Item', result)
        self.assertIn('Header', result)

    def test_handles_malformed_html(self) -> None:
        """Verify unclosed tags do not break parsing and content is preserved."""

        html = '<div><p>Unclosed paragraph<div>Another div</div>'
        result = sanitize_html(html)
        self.assertIn('Unclosed paragraph', result)
        self.assertIn('Another div', result)

    def test_handles_unicode_content(self) -> None:
        """Verify Unicode characters and emojis are preserved."""

        html = '<p>Unicode: 你好世界 🎉 émojis</p>'
        result = sanitize_html(html)
        self.assertIn('你好世界', result)
        self.assertIn('🎉', result)
        self.assertIn('émojis', result)
