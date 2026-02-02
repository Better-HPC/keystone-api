"""Low level utilities for processing and manipulating HTML notifications."""

import re

import nh3

__all__ = ["sanitize_html"]


def _sanitize_css(css: str) -> str:
    """Remove external resources and JavaScript from CSS."""

    # Remove @import rules
    css = re.sub(r'@import\s+[^;]+;', '', css, flags=re.IGNORECASE)

    # Remove @font-face blocks (external font loading)
    css = re.sub(r'@font-face\s*\{[^}]*\}', '', css, flags=re.IGNORECASE | re.DOTALL)

    # Remove url() with external URLs (http, https, //)
    # Keeps data: URIs and relative paths
    css = re.sub(
        r'url\s*\(\s*["\']?\s*(https?://|//)[^)]*\)',
        'url()',
        css,
        flags=re.IGNORECASE
    )

    # Remove expression() - IE JS execution
    css = re.sub(r'expression\s*\([^)]*\)', '', css, flags=re.IGNORECASE)

    # Remove behavior: property - IE JS execution
    css = re.sub(r'behavior\s*:\s*[^;]+;?', '', css, flags=re.IGNORECASE)

    # Remove -moz-binding: property - Firefox XBL
    css = re.sub(r'-moz-binding\s*:\s*[^;]+;?', '', css, flags=re.IGNORECASE)

    return css


def _sanitize_css_in_html(html: str) -> str:
    """Sanitize CSS in both style attributes and style tags."""

    # Sanitize inline style attributes
    html = re.sub(
        r'style="([^"]*)"',
        lambda m: f'style="{_sanitize_css(m.group(1))}"',
        html,
        flags=re.IGNORECASE
    )

    # Sanitize <style> tag content
    html = re.sub(
        r'(<style[^>]*>)(.*?)(</style>)',
        lambda m: m.group(1) + _sanitize_css(m.group(2)) + m.group(3),
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    return html


def _sanitize_html_tags(html: str) -> str:
    """Sanitize the given HTML string.

    Only allows whitelisted tags and attributes in HTML code.
    Javascript is removed entirely.
    """

    # Only allow whitelisted tags and attributes
    clean = nh3.clean(
        html=html,
        tags={
            'a', 'abbr', 'acronym', 'area', 'article', 'aside', 'b', 'bdi',
            'bdo', 'blockquote', 'br', 'caption', 'center', 'cite', 'code',
            'col', 'colgroup', 'data', 'dd', 'del', 'details', 'dfn', 'div',
            'dl', 'dt', 'em', 'figcaption', 'figure', 'font', 'footer', 'h1',
            'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i',
            'img', 'ins', 'kbd', 'li', 'map', 'mark', 'nav', 'ol', 'p', 'pre',
            'q', 'rp', 'rt', 'rtc', 'ruby', 's', 'samp', 'small', 'span',
            'strike', 'strong', 'style', 'sub', 'summary', 'sup', 'table',
            'tbody', 'td', 'th', 'thead', 'time', 'title', 'tr', 'tt', 'u',
            'ul', 'var', 'wbr'
        },
        clean_content_tags=set(),
        strip_comments=True,
        link_rel="noopener noreferrer",
        url_schemes={"http", "https", "mailto"},
        attributes={
            "*": {
                "accesskey", "aria-atomic", "aria-busy", "aria-controls", "aria-describedby", "aria-expanded",
                "aria-hidden", "aria-label", "aria-labelledby", "aria-live", "aria-relevant", "class",
                "contenteditable", "dir", "draggable", "hidden", "id", "lang", "role", "spellcheck", "style",
                "tabindex", "title", "translate",
            },
            "a": {"download", "href", "hreflang", "name", "target", "type"},
            "abbr": {"title"},
            "area": {"alt", "coords", "download", "href", "rel", "shape", "target"},
            "bdi": set(),
            "bdo": {"dir"},
            "blockquote": {"cite"},
            "caption": {"align"},
            "center": set(),
            "col": {"align", "span", "valign", "width"},
            "colgroup": {"align", "span", "valign", "width"},
            "data": {"value"},
            "del": {"cite", "datetime"},
            "details": {"name", "open"},
            "dfn": {"title"},
            "div": {"align"},
            "figcaption": set(),
            "figure": set(),
            "font": {"color", "face", "size"},
            "h1": {"align"},
            "h2": {"align"},
            "h3": {"align"},
            "h4": {"align"},
            "h5": {"align"},
            "h6": {"align"},
            "hr": {"align", "noshade", "size", "width"},
            "img": {"alt", "border", "crossorigin", "decoding", "height", "ismap", "loading", "sizes", "src", "srcset", "usemap", "width", },
            "ins": {"cite", "datetime"},
            "li": {"type", "value"},
            "map": {"name"},
            "ol": {"reversed", "start", "type"},
            "p": {"align"},
            "pre": {"width"},
            "q": {"cite"},
            "summary": set(),
            "table": {"align", "bgcolor", "border", "cellpadding", "cellspacing", "frame", "height", "rules", "summary", "width"},
            "tbody": {"align", "valign"},
            "td": {"abbr", "align", "bgcolor", "colspan", "headers", "height", "nowrap", "rowspan", "scope", "valign", "width"},
            "tfoot": {"align", "valign"},
            "th": {"abbr", "align", "bgcolor", "colspan", "headers", "height", "nowrap", "rowspan", "scope", "valign", "width"},
            "thead": {"align", "valign"},
            "time": {"datetime"},
            "tr": {"align", "bgcolor", "valign"},
            "ul": {"type"},
        },
    )

    return clean


def sanitize_html(html: str) -> str:
    """Sanitize HTML for safe display in a web frontend.

    Removes:
        - JavaScript (script tags, event handlers, javascript: URLs)
        - Dangerous CSS (external URLs, @import, @font-face, expressions)
        - Disallowed tags and attributes

    Preserves:
        - Safe HTML tags and attributes
        - Inline styles (with external URLs removed)
        - Style tags (with external URLs removed)

    Args:
        html: The raw HTML string to sanitize.

    Returns:
        Sanitized HTML string safe for display.
    """

    html = _sanitize_html_tags(html)
    html = _sanitize_css_in_html(html)
    return html
