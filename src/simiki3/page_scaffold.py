"""Utilities for creating new wiki pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .config import SiteConfig
from .utils import current_timestamp, slugify


@dataclass
class NewPageResult:
    path: Path
    created: bool
    slug: str


class PageExistsError(FileExistsError):
    """Raised when attempting to create a page that already exists."""


class InvalidPagePathError(ValueError):
    """Raised when a page category would escape the site content directory."""


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
    category = (category or "").strip()
    if category.startswith(("/", "\\")):
        raise InvalidPagePathError("category must be a relative path")
    category = category.strip("/")
    if "\\" in category or ".." in Path(category).parts:
        raise InvalidPagePathError("category must stay inside the content directory")
    if "\n" in title or "\r" in title:
        raise ValueError("title must be a single line")
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

    metadata = {
        "title": title,
        "date": current_timestamp(),
        "category": category,
    }
    if draft:
        metadata["draft"] = True
    front_matter = yaml.safe_dump(
        metadata, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).strip()
    page_content = (
        f"---\n{front_matter}\n---\n\n"
        f"# {title}\n\n"
        "Start writing here.\n"
    )
    page_path.write_text(page_content, encoding="utf-8")

    return NewPageResult(path=page_path, created=True, slug=slug_value)
