"""Validation helpers for comparing build outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import difflib


@dataclass
class ValidationResult:
    missing_in_new: list[Path] = field(default_factory=list)
    missing_in_legacy: list[Path] = field(default_factory=list)
    changed_files: list[Path] = field(default_factory=list)
    diffs: dict[Path, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return not (self.missing_in_new or self.missing_in_legacy or self.changed_files)


def compare_directories(legacy: Path, new: Path, *, extensions: Sequence[str] | None = None, diff_limit: int = 2048) -> ValidationResult:
    legacy = Path(legacy).resolve()
    new = Path(new).resolve()
    result = ValidationResult()

    if extensions is not None:
        exts = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions}
        def allowed(path: Path) -> bool:
            return path.suffix.lower() in exts
    else:
        def allowed(path: Path) -> bool:  # type: ignore
            return True

    legacy_files = _collect_files(legacy, allowed)
    new_files = _collect_files(new, allowed)

    legacy_keys = set(legacy_files.keys())
    new_keys = set(new_files.keys())

    for key in sorted(legacy_keys - new_keys):
        result.missing_in_new.append(key)
    for key in sorted(new_keys - legacy_keys):
        result.missing_in_legacy.append(key)

    for key in sorted(legacy_keys & new_keys):
        legacy_bytes = legacy_files[key].read_bytes()
        new_bytes = new_files[key].read_bytes()
        if legacy_bytes != new_bytes:
            result.changed_files.append(key)
            diff_text = _render_diff(legacy_bytes, new_bytes, legacy_files[key], new_files[key], limit=diff_limit)
            if diff_text:
                result.diffs[key] = diff_text

    return result


def _collect_files(root: Path, predicate) -> Dict[Path, Path]:
    files: Dict[Path, Path] = {}
    for path in root.rglob('*'):
        if path.is_file() and predicate(path):
            files[path.relative_to(root)] = path
    return files


def _render_diff(legacy_bytes: bytes, new_bytes: bytes, legacy_path: Path, new_path: Path, *, limit: int) -> str:
    try:
        legacy_text = legacy_bytes.decode('utf-8')
        new_text = new_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return ''

    diff_lines = difflib.unified_diff(
        legacy_text.splitlines(),
        new_text.splitlines(),
        fromfile=str(legacy_path),
        tofile=str(new_path),
        lineterm='')
    snippet = '
'.join(list(diff_lines)[:limit])
    return snippet

