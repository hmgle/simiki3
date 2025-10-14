"""Synchronisation utilities for updating site scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Iterable, List

from .config import ConfigFiles, SiteConfig, load_config
from .theme import builtin_themes, sync_theme_to_site
from .utils import current_timestamp

PACKAGE_SITE_UPDATE = "simiki3.data.site_update"


@dataclass
class UpdateResult:
    copied_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)
    theme_synced: list[str] = field(default_factory=list)

    def record(self, destination: Path, *, copied: bool) -> None:
        collection = self.copied_files if copied else self.skipped_files
        rel = destination
        if rel not in collection:
            collection.append(rel)


class SiteUpdater:
    """Copy built-in update assets into an existing wiki."""

    def __init__(self, root: Path, config: SiteConfig) -> None:
        self.root = Path(root).resolve()
        self.config = config
        self.resources = resources.files(PACKAGE_SITE_UPDATE)

    def update(self, *, overwrite: bool = False, include_examples: bool = False, sync_theme: bool = False) -> UpdateResult:
        result = UpdateResult()

        self._copy_templates(overwrite=overwrite, result=result)
        if include_examples:
            self._copy_examples(overwrite=overwrite, result=result)
        if sync_theme:
            self._sync_theme(result=result, overwrite=overwrite)
        return result

    def _copy_templates(self, *, overwrite: bool, result: UpdateResult) -> None:
        for resource in ("_config.yml.in", "fabfile.py", "Dockerfile"):
            destination = self.root / resource
            self._copy_resource(self.resources / resource, destination, overwrite, result)

    def _copy_examples(self, *, overwrite: bool, result: UpdateResult) -> None:
        examples_dir = self.resources / "examples"
        if not resources.is_resource(examples_dir, "__init__") and not examples_dir.exists():
            return
        with resources.as_file(examples_dir) as extracted:
            src_path = Path(extracted)
            for item in src_path.rglob("*"):
                if item.is_dir():
                    continue
                rel = item.relative_to(src_path)
                destination = self.root / rel
                self._copy_file(item, destination, overwrite, result)

    def _sync_theme(self, *, result: UpdateResult, overwrite: bool) -> None:
        available = builtin_themes()
        theme_name = self.config.theme
        if theme_name not in available:
            return
        sync_theme_to_site(self.root, self.config, theme_name, force=overwrite)
        result.theme_synced.append(theme_name)

    def _copy_resource(self, resource, destination: Path, overwrite: bool, result: UpdateResult) -> None:
        with resources.as_file(resource) as extracted:
            src_path = Path(extracted)
            self._copy_file(src_path, destination, overwrite, result)

    def _copy_file(self, src: Path, destination: Path, overwrite: bool, result: UpdateResult) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not overwrite:
            result.record(destination.relative_to(self.root), copied=False)
            return
        data = src.read_bytes()
        destination.write_bytes(data)
        result.record(destination.relative_to(self.root), copied=True)


def update_site(
    root: Path,
    *,
    overwrite: bool = False,
    include_examples: bool = False,
    sync_theme: bool = False,
    config: SiteConfig | None = None,
) -> UpdateResult:
    root = Path(root).resolve()
    if config is None:
        config = load_config(ConfigFiles().resolve(root))
    updater = SiteUpdater(root, config)
    return updater.update(overwrite=overwrite, include_examples=include_examples, sync_theme=sync_theme)

