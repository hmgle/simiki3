"""Utilities for creating new wiki pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import SiteConfig
from .utils import current_timestamp, slugify


@dataclass
class NewPageResult:
    path: Path
    created: bool
    slug: str


class PageExistsError(FileExistsError):
    """Raised when attempting to create a page that already exists."""


def create_page(
    root: Path,
    config: SiteConfig,
    *,
    title: str,
    category: str = "intro",
    slug: Optional[str] = None,
    draft: bool = False,
    force: bool = False,
) -> NewPageResult:
    """Create a new markdown page under the site's content directory."""

    root = Path(root)
    category = (category or "").strip("/ ")
    slug_value = slugify(slug or title)

    relative_dir = Path(config.source)
    if category:
        relative_dir /= Path(category)
    target_dir = root / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slug_value}.{config.default_ext}"
    page_path = target_dir / filename

    if page_path.exists() and not force:
        raise PageExistsError(f"Page already exists: {page_path}")

    metadata_lines = [
        "---",
        f"title: \"{title}\"",
        f"date: {current_timestamp()}",
        f"category: {category}",
    ]
    if draft:
        metadata_lines.append("draft: true")
    metadata_lines.append("---\n")

    body = (
        "# {title}\n\n"
        "Start writing here.\n"
    ).format(title=title)

    page_content = "\n".join(metadata_lines) + body
    page_path.write_text(page_content, encoding="utf-8")

    return NewPageResult(path=page_path, created=True, slug=slug_value)
