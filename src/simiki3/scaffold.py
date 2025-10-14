"""Site scaffolding helpers for the Simiki3 rewrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable

import yaml

from .config import ConfigFiles, SiteConfig, default_config

_TEMPLATES_PACKAGE = "simiki3.data.site_template"
_DEFAULT_THEME_NAME = "default"
_DEMO_CATEGORY = "intro"
_DEMO_FILENAME = "welcome.md"


@dataclass
class InitResult:
    """Summary of files and directories touched during init."""

    target: Path
    created_dirs: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def record_dir(self, path: Path) -> None:
        rel = _relative(self.target, path)
        if rel not in self.created_dirs:
            self.created_dirs.append(rel)

    def record_file(self, path: Path) -> None:
        rel = _relative(self.target, path)
        if rel not in self.created_files:
            self.created_files.append(rel)

    def record_skipped(self, path: Path) -> None:
        rel = _relative(self.target, path)
        if rel not in self.skipped:
            self.skipped.append(rel)


def initialise_site(
    target: Path,
    *,
    config: SiteConfig | None = None,
    force: bool = False,
) -> InitResult:
    """Create a new wiki skeleton under ``target``.

    Parameters
    ----------
    target:
        Directory where the site should be created.
    config:
        Optional configuration overrides. Defaults to :func:`default_config`.
    force:
        When ``True``, existing files are overwritten instead of aborting.
    """

    target = Path(target).expanduser().resolve()
    config = config or default_config()

    if target.exists() and not target.is_dir():
        raise NotADirectoryError(f"Target path exists and is not a directory: {target}")

    target.mkdir(parents=True, exist_ok=True)

    critical = _critical_paths(target, config)
    existing = [path for path in critical if path.exists()]
    if existing and not force:
        rels = ", ".join(sorted(_relative(target, path) or "." for path in existing))
        raise FileExistsError(
            f"Refusing to overwrite existing site content in {target}: {rels}"
        )

    result = InitResult(target=target)

    # Core directories
    for directory in _required_directories(target, config):
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            result.record_dir(directory)

    # Attachments placeholder
    _write_file(target / config.attach / ".gitkeep", "", force=force, result=result)

    # Write configuration file
    config_file = ConfigFiles().resolve(target)
    _write_yaml(config_file, config.as_dict(), force=force, result=result)

    # Demo content
    demo_category_dir = target / config.source / _DEMO_CATEGORY
    if not demo_category_dir.exists():
        demo_category_dir.mkdir(parents=True, exist_ok=True)
        result.record_dir(demo_category_dir)
    demo_page = demo_category_dir / _DEMO_FILENAME
    demo_content = _demo_markdown(config)
    _write_file(demo_page, demo_content, force=force, result=result)

    # Copy embedded theme assets
    _copy_theme_assets(target, config, force=force, result=result)

    return result


def _critical_paths(target: Path, config: SiteConfig) -> list[Path]:
    theme_root = Path(config.themes_dir) / _DEFAULT_THEME_NAME
    return [
        ConfigFiles().resolve(target),
        target / config.source,
        target / config.destination,
        target / config.attach,
        target / theme_root,
    ]


def _required_directories(target: Path, config: SiteConfig) -> Iterable[Path]:
    theme_root = Path(config.themes_dir) / _DEFAULT_THEME_NAME
    return [
        target / config.source,
        target / config.destination,
        target / config.attach,
        target / config.themes_dir,
        target / theme_root,
    ]


def _write_yaml(path: Path, data: dict, *, force: bool, result: InitResult) -> None:
    if path.exists() and not force:
        result.record_skipped(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
    result.record_file(path)


def _write_file(path: Path, content: str | bytes, *, force: bool, result: InitResult) -> None:
    if path.exists() and not force:
        result.record_skipped(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    result.record_file(path)


def _copy_theme_assets(target: Path, config: SiteConfig, *, force: bool, result: InitResult) -> None:
    theme_root = resources.files(_TEMPLATES_PACKAGE) / "themes" / _DEFAULT_THEME_NAME
    destination_root = target / config.themes_dir / _DEFAULT_THEME_NAME

    for entry in theme_root.rglob("*"):
        relative = Path(entry.relative_to(theme_root))
        destination = destination_root / relative
        if entry.is_dir():
            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)
                result.record_dir(destination)
            continue
        data = entry.read_bytes()
        _write_file(destination, data, force=force, result=result)


def _demo_markdown(config: SiteConfig) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return (
        "---\n"
        f"title: Welcome to {config.title}\n"
        f"date: {timestamp}\n"
        f"category: {_DEMO_CATEGORY}\n"
        "---\n\n"
        "# Hello, Simiki3!\n\n"
        "You have created a new wiki powered by **Simiki3**. Edit the files under "
        f"`{config.source}/` to add more pages, then run `simiki3 build` to render your site.\n\n"
        "## Next steps\n\n"
        "- Create additional markdown files inside the category directories.\n"
        "- Adjust the site metadata in `_config.yml`.\n"
        f"- Customise the theme in `{config.themes_dir}/{_DEFAULT_THEME_NAME}`.\n"
    )


def _relative(target: Path, path: Path) -> str:
    try:
        rel = path.relative_to(target)
    except ValueError:
        return str(path)
    return str(rel) if str(rel) else "."
