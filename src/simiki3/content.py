"""Content discovery and parsing utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from markdown import markdown

from .config import SiteConfig

_FRONT_MATTER_DELIM = "---"
_DEFAULT_EXTENSIONS = {"md", "markdown", "mdown", "mkd"}


class PageError(RuntimeError):
    """Raised when a page cannot be parsed."""


@dataclass
class Page:
    source_path: Path
    relative_path: Path
    meta: dict[str, Any]
    markdown: str
    html: str

    @property
    def output_relative(self) -> Path:
        return self.relative_path.with_suffix(".html")

    @property
    def category(self) -> str:
        parent = self.relative_path.parent
        if not parent.parts:
            return ""
        return parent.as_posix()


def discover_markdown_files(source_dir: Path, *, config: SiteConfig) -> list[Path]:
    """Return markdown files under ``source_dir`` respecting hidden folders."""
    source_dir = source_dir.resolve()
    if not source_dir.exists():
        return []
    allowed = {config.default_ext.lower(), *_DEFAULT_EXTENSIONS}
    files: list[Path] = []
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith('.'):
            continue
        try:
            relative = path.relative_to(source_dir)
        except ValueError:
            continue
        if any(part.startswith('.') for part in relative.parts):
            continue
        if path.suffix.lower().lstrip('.') not in allowed:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(source_dir).as_posix())


def load_page(path: Path, *, source_dir: Path, config: SiteConfig) -> Page:
    """Load a markdown page, parsing YAML front matter and rendering to HTML."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PageError(f"Page is not valid UTF-8: {path}") from exc
    meta_text, markdown_text = _split_front_matter(text)

    try:
        meta = yaml.safe_load(meta_text) if meta_text.strip() else {}
    except yaml.YAMLError as exc:
        raise PageError(f"Invalid YAML front matter in {path}: {exc}") from exc

    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise PageError(f"Front matter for {path} must be a mapping")

    relative = path.relative_to(source_dir)
    meta.setdefault("title", _derive_title(relative))
    meta.setdefault("category", relative.parent.as_posix() if relative.parent.parts else "")

    md_extensions = ["fenced_code", "tables", "toc"]
    if config.pygments:
        md_extensions.append("codehilite")

    html = markdown(markdown_text, extensions=md_extensions, output_format="html5")

    return Page(
        source_path=path,
        relative_path=relative,
        meta=meta,
        markdown=markdown_text,
        html=html,
    )


def _split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines:
        return "", ""
    if lines[0].strip() != _FRONT_MATTER_DELIM:
        return "", text

    meta_lines = []
    idx = 1
    while idx < len(lines):
        if lines[idx].strip() == _FRONT_MATTER_DELIM:
            break
        meta_lines.append(lines[idx])
        idx += 1
    else:
        raise PageError("Unclosed YAML front matter")

    body_lines = lines[idx + 1 :]
    meta_text = "\n".join(meta_lines)
    body_text = "\n".join(body_lines)
    return meta_text, body_text


def _derive_title(relative: Path) -> str:
    raw = relative.stem.replace('-', ' ').replace('_', ' ')
    title = raw.strip().title() or "Untitled"
    return title
