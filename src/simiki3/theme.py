"""Theme loading and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from .config import SiteConfig


THEME_PACKAGE = "simiki3.data.site_template.themes"


class ThemeError(RuntimeError):
    """Raised when the requested theme cannot be rendered."""


@dataclass(frozen=True)
class ThemePaths:
    root: Path
    templates: Path
    static: Path


class ThemeRenderer:
    """Render site templates from the configured theme."""

    def __init__(self, theme_root: Path) -> None:
        if not theme_root.exists():
            raise ThemeError(f"Theme directory does not exist: {theme_root}")

        templates = theme_root / "templates"
        if not templates.exists():
            raise ThemeError(f"Theme templates directory missing: {templates}")

        self.paths = ThemePaths(root=theme_root, templates=templates, static=theme_root / "static")
        self.env = Environment(
            loader=FileSystemLoader(str(self.paths.templates)),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
        )

    def render(self, layout: str, *, context: dict) -> str:
        """Render the given ``layout`` (e.g. ``page``) using ``context``."""
        template_name = f"{layout}.html"
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            try:
                template = self.env.get_template("page.html")
            except TemplateNotFound as exc:  # pragma: no cover
                raise ThemeError(f"Theme does not provide a 'page.html' template") from exc
        return template.render(context)


def builtin_themes() -> List[str]:
    """Return the list of built-in theme names shipped with Simiki3."""
    base = resources.files(THEME_PACKAGE)
    return sorted([entry.name for entry in base.iterdir() if entry.is_dir()])


@dataclass
class ThemeSyncResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    overwritten: list[Path] = field(default_factory=list)

    def record(self, path: Path, *, status: str) -> None:
        relative = path
        if status == "created":
            if relative not in self.created:
                self.created.append(relative)
        elif status == "skipped":
            if relative not in self.skipped:
                self.skipped.append(relative)
        elif status == "overwritten":
            if relative not in self.overwritten:
                self.overwritten.append(relative)


def sync_theme_to_site(
    root: Path,
    config: SiteConfig,
    theme_name: str,
    *,
    force: bool = False,
) -> ThemeSyncResult:
    """Copy a bundled theme into the site's themes directory."""

    theme_name = theme_name.strip()
    available = builtin_themes()
    if theme_name not in available:
        raise ThemeError(f"Unknown theme '{theme_name}'. Available: {', '.join(available)}")

    target_root = Path(root).resolve() / config.themes_dir / theme_name
    source_root = resources.files(THEME_PACKAGE) / theme_name

    result = ThemeSyncResult()
    target_root.mkdir(parents=True, exist_ok=True)

    with resources.as_file(source_root) as extracted:
        src_path = Path(extracted)
        for entry in src_path.rglob("*"):
            if entry.is_dir():
                continue
            relative = entry.relative_to(src_path)
            destination = target_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            existed = destination.exists()
            if existed and not force:
                result.record(relative, status="skipped")
                continue

            destination.write_bytes(entry.read_bytes())
            status = "overwritten" if existed and force else "created"
            result.record(relative, status=status)

    return result
