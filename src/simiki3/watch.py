"""Filesystem watch helpers built on top of watchfiles."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from watchfiles import Change, DefaultFilter, watch

from .build import BuildResult, build_site
from .config import ConfigFiles, load_config

ChangeEvent = Tuple[Change, str]


@dataclass
class BuildWatcher:
    """Watch filesystem changes and trigger site rebuilds."""

    root: Path
    include_drafts: bool = False
    debounce_ms: int = 350
    build_fn: Optional[Callable[[], BuildResult]] = None
    on_rebuild: Optional[Callable[[BuildResult, Sequence[ChangeEvent]], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._filter = self._create_filter()
        if self.build_fn is None:
            self.build_fn = lambda: build_site(self.root, include_drafts=self.include_drafts)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=5)

    def _loop(self) -> None:
        try:
            for changes in watch(
                str(self.root),
                stop_event=self._stop_event,
                watch_filter=self._filter,
                debounce=self.debounce_ms,
            ):
                if not changes:
                    continue
                try:
                    result = self.build_fn() if self.build_fn else None
                except Exception as exc:  # pragma: no cover - delegated to error handler
                    if self.on_error:
                        self.on_error(exc)
                    continue
                if self.on_rebuild and result is not None:
                    self.on_rebuild(result, tuple(changes))
        finally:
            self._stop_event.set()

    def _create_filter(self) -> DefaultFilter:
        try:
            config = load_config(ConfigFiles().resolve(self.root))
            destination = config.destination
        except FileNotFoundError:
            destination = "output"
        ignore_dirs = {destination, ".git", "__pycache__", "htmlcov", "build", "dist"}
        return DefaultFilter(ignore_dirs=ignore_dirs)
