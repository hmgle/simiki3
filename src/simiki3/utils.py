"""General utility helpers for Simiki3."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def write_file(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write text content to ``path`` ensuring parent directories exist."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def strip_html(value: str, *, collapse_whitespace: bool = True) -> str:
    """Remove HTML tags from ``value`` and optionally collapse whitespace."""
    text = _HTML_TAG_RE.sub("", value or "")
    if collapse_whitespace:
        text = " ".join(text.split())
    return text.strip()


_SLUG_ALLOWED = re.compile(r"[^a-z0-9-]")


def slugify(value: str, *, default: str = "page") -> str:
    """Convert ``value`` to a filesystem-friendly slug."""
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[\s/_]+", "-", value)
    value = _SLUG_ALLOWED.sub("", value)
    value = value.strip("-")
    return value or default


def current_timestamp() -> str:
    """Return an ISO-8601 timestamp in UTC without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
