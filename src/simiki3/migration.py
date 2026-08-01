"""Utilities to help migrate legacy Simiki sites to Simiki3."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Tuple

from rich.console import Console
from rich.table import Table

from .config import ConfigError, ConfigFiles, SiteConfig
from .content import PageError, discover_markdown_files, load_page
from .utils import current_timestamp
import shutil
import yaml
from .theme import builtin_themes, sync_theme_to_site


@dataclass
class PageIssue:
    path: Path
    message: str
    suggestion: str | None = None


@dataclass
class MigrationReport:
    config_warnings: list[str] = field(default_factory=list)
    page_issues: list[PageIssue] = field(default_factory=list)
    theme_warnings: list[str] = field(default_factory=list)

    @property
    def has_blockers(self) -> bool:
        return any(
            "layout" in issue.message or "cannot be parsed" in issue.message
            for issue in self.page_issues
        )

    @property
    def issue_count(self) -> int:
        return len(self.page_issues)

    def display(self, console: Console) -> None:
        if self.config_warnings:
            table = Table(title="Configuration Warnings")
            table.add_column("Warning", style="yellow")
            for warning in self.config_warnings:
                table.add_row(warning)
            console.print(table)

        if self.theme_warnings:
            table = Table(title="Theme Warnings")
            table.add_column("Warning", style="yellow")
            for warning in self.theme_warnings:
                table.add_row(warning)
            console.print(table)

        if self.page_issues:
            table = Table(title="Page Issues")
            table.add_column("Page", style="cyan")
            table.add_column("Issue", style="red")
            table.add_column("Suggestion", style="green")
            for issue in self.page_issues:
                table.add_row(str(issue.path), issue.message, issue.suggestion or "")
            console.print(table)

        if not any([self.config_warnings, self.theme_warnings, self.page_issues]):
            console.print("[green]No migration issues detected.[/green]")


LEGACY_LAYOUT_VALUES = {"post"}


def analyse_site(root: Path, config: SiteConfig) -> MigrationReport:
    """Inspect the given site for legacy compatibility problems."""

    root = Path(root)
    report = MigrationReport()

    if config.theme not in builtin_themes():
        report.theme_warnings.append(
            f"Theme '{config.theme}' is not bundled with simiki3; run `simiki3 theme sync` or port it manually."
        )

    markdown_files = discover_markdown_files(root / config.source, config=config)
    for file_path in markdown_files:
        relative = file_path.relative_to(root / config.source)
        rel_path = Path(config.source) / relative
        try:
            page = load_page(file_path, source_dir=root / config.source, config=config)
        except (PageError, UnicodeDecodeError) as exc:
            report.page_issues.append(
                PageIssue(
                    path=rel_path,
                    message=f"page cannot be parsed: {exc}",
                    suggestion="Fix the front matter or file encoding before migrating",
                )
            )
            continue

        layout = page.meta.get("layout")
        if layout in LEGACY_LAYOUT_VALUES:
            report.page_issues.append(
                PageIssue(
                    path=rel_path,
                    message=f"legacy layout '{layout}' detected",
                    suggestion="Update front matter to use layout: page",
                )
            )

        if "title" not in page.meta or not page.meta["title"]:
            report.page_issues.append(
                PageIssue(
                    path=rel_path,
                    message="missing title in front matter",
                    suggestion="Add a `title` key or rerun `simiki3 new` to scaffold",
                )
            )

        if "date" not in page.meta:
            report.page_issues.append(
                PageIssue(
                    path=rel_path,
                    message="missing date field",
                    suggestion="Set `date: YYYY-MM-DD` for Atom feed ordering",
                )
            )

    if not markdown_files:
        report.config_warnings.append("No markdown files found under content directory; verify legacy site copy.")

    return report


@dataclass
class FixAction:
    path: Path
    description: str


@dataclass
class FixSummary:
    config_updated: bool = False
    config_path: Path | None = None
    page_actions: list[FixAction] = field(default_factory=list)
    theme_synced: bool = False
    theme_name: str | None = None

    @property
    def pages_updated(self) -> int:
        return len(self.page_actions)


def apply_fixes(
    root: Path,
    config: SiteConfig,
    *,
    fix_config_file: bool = True,
    fix_pages: bool = True,
    sync_theme: bool = False,
    backup: bool = True,
    dry_run: bool = False,
) -> FixSummary:
    """Apply automatic migration fixes to the site."""

    summary = FixSummary()
    root = Path(root)

    if fix_config_file:
        config_actions = _fix_config_file(root, dry_run=dry_run, backup=backup)
        if config_actions:
            summary.config_updated = not dry_run
            summary.config_path = ConfigFiles().resolve(root)

    if fix_pages:
        for action in _fix_pages(root, config, dry_run=dry_run, backup=backup):
            summary.page_actions.append(action)

    if sync_theme:
        available = builtin_themes()
        theme_name = config.theme
        summary.theme_name = theme_name
        theme_dir = root / config.themes_dir / theme_name
        requires_sync = theme_name in available and not (theme_dir / "templates").exists()
        if theme_name in available and requires_sync:
            summary.theme_synced = True
            if not dry_run:
                sync_theme_to_site(root, config, theme_name, force=False)
    return summary


def _fix_config_file(root: Path, *, dry_run: bool, backup: bool) -> list[str]:
    config_path = ConfigFiles().resolve(root)
    if not config_path.exists():
        return []

    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a mapping of keys to values")

    changed = False

    url = data.get("url")
    if isinstance(url, str) and url.endswith("/"):
        data["url"] = url.rstrip("/")
        changed = True

    root_value = data.get("root")
    if isinstance(root_value, str):
        stripped = root_value.strip() or "/"
        if not stripped.startswith("/"):
            stripped = f"/{stripped}"
        parts = [part for part in stripped.split("/") if part]
        normalised_root = "/" + "/".join(parts) if parts else "/"
        if normalised_root != root_value:
            data["root"] = normalised_root
            changed = True

    theme = data.get("theme")
    if isinstance(theme, str):
        candidate = theme.strip()
        if candidate and candidate != theme:
            data["theme"] = candidate
            changed = True

    if changed and not dry_run:
        if backup and config_path.exists():
            _write_backup(config_path)
        with config_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)

    return ["_config.yml"] if changed else []


def _fix_pages(root: Path, config: SiteConfig, *, dry_run: bool, backup: bool) -> Iterable[FixAction]:
    content_dir = root / config.source
    if not content_dir.exists():
        return []

    actions: list[FixAction] = []
    markdown_files = discover_markdown_files(content_dir, config=config)
    for file_path in markdown_files:
        action_descriptions = _fix_single_page(file_path, config, dry_run=dry_run, backup=backup)
        for desc in action_descriptions:
            actions.append(FixAction(path=file_path.relative_to(root), description=desc))
    return actions


def _fix_single_page(path: Path, config: SiteConfig, *, dry_run: bool, backup: bool) -> list[str]:
    original_text = path.read_text(encoding="utf-8")
    meta_str, body_str = _split_front_matter(original_text)
    try:
        meta = yaml.safe_load(meta_str) if meta_str.strip() else {}
    except yaml.YAMLError:
        return []
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        # unsupported format; skip modifications
        return []

    changes: list[str] = []

    layout = meta.get("layout")
    if layout in LEGACY_LAYOUT_VALUES:
        meta["layout"] = "page"
        changes.append("layout -> page")

    if "date" not in meta or not meta.get("date"):
        meta["date"] = current_timestamp()
        changes.append("date added")

    if not changes:
        return []

    if not dry_run:
        if backup and path.exists():
            _write_backup(path)
        dumped = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
        new_text = "---\n" + dumped + "\n---\n"
        if body_str:
            if not body_str.startswith("\n"):
                new_text += "\n"
            new_text += body_str.lstrip("\n")
        new_text = new_text.rstrip() + "\n"
        path.write_text(new_text, encoding="utf-8")

    return changes


def _split_front_matter(text: str) -> Tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text

    meta_lines: list[str] = []
    idx = 1
    while idx < len(lines):
        if lines[idx].strip() == "---":
            body = "\n".join(lines[idx + 1 :])
            return "\n".join(meta_lines), body
        meta_lines.append(lines[idx])
        idx += 1

    return "", text


def _write_backup(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    counter = 1
    while backup_path.exists():
        backup_path = path.with_suffix(path.suffix + f".bak{counter}")
        counter += 1
    shutil.copy2(path, backup_path)
