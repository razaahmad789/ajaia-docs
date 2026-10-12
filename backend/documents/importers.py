"""Convert an uploaded text/markdown file into editor-ready HTML.

Supported types are intentionally limited to plain text and Markdown. This is
stated in the UI and README. The uploaded bytes are parsed in memory and only
the resulting HTML is persisted (as a Document) — we never store the raw file,
which keeps deployment simple (no media volume) and avoids ephemeral-disk loss
on hosts like Render's free tier.
"""
import html
import os

import markdown

from .sanitize import sanitize_html

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}


class ImportError_(Exception):
    """Raised when an uploaded file cannot be imported."""


def _decode(raw_bytes: bytes) -> str:
    """Decode uploaded bytes as UTF-8, falling back to latin-1."""
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return raw_bytes.decode("latin-1", errors="replace")


def plaintext_to_html(text: str) -> str:
    """Wrap each non-empty line/block of plain text in a paragraph."""
    blocks = text.replace("\r\n", "\n").split("\n\n")
    paragraphs = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        # Preserve single newlines within a block as <br>.
        escaped = html.escape(stripped).replace("\n", "<br>")
        paragraphs.append(f"<p>{escaped}</p>")
    return "".join(paragraphs) or "<p></p>"


def markdown_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "nl2br"],
    )


def import_file(filename: str, raw_bytes: bytes) -> tuple[str, str]:
    """Return ``(title, sanitized_html)`` for an uploaded file.

    ``title`` defaults to the filename without extension. Raises
    ``ImportError_`` for unsupported extensions.
    """
    base, ext = os.path.splitext(filename or "")
    ext = ext.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ImportError_(
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    text = _decode(raw_bytes)
    if ext in MARKDOWN_EXTENSIONS:
        raw_html = markdown_to_html(text)
    else:
        raw_html = plaintext_to_html(text)

    title = (base or "Imported document").strip()[:255]
    return title, sanitize_html(raw_html)
