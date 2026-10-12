"""HTML sanitization for document content.

Document content is user-supplied HTML produced by the TipTap editor (or by
importing a file). We never trust it: before persisting we strip it down to the
small set of tags/attributes our editor actually uses. This prevents stored XSS
(e.g. ``<script>`` or ``onerror=`` injected via the API or a crafted import)
while preserving the formatting the product supports.
"""
import bleach

# Tags that map to the formatting the editor exposes:
# bold, italic, underline, strike, headings, lists, paragraphs, links, code,
# blockquotes and horizontal rules.
ALLOWED_TAGS = [
    "p", "br", "hr",
    "strong", "b", "em", "i", "u", "s", "strike",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "code", "pre",
    "a", "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
    "code": ["class"],
}

# Only safe URL schemes for links.
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(raw: str) -> str:
    """Return a sanitized copy of ``raw`` HTML safe to store and re-render."""
    if not raw:
        return ""
    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned
