from pathlib import Path

import pytest
from watchfiles import Change

from simiki3.watch import BuildWatcher


def test_build_watcher_triggers_build(monkeypatch, tmp_path):
    root = tmp_path
    events = [{(Change.added, str(root / "content" / "file.md"))}]

    def fake_watch(*args, **kwargs):
        for event in events:
            yield event

    monkeypatch.setattr("simiki3.watch.watch", fake_watch)

    calls = []

    def build_fn():
        calls.append(True)
        class Dummy:
            rendered = []
            skipped = []
        return Dummy()

    watcher = BuildWatcher(root=root, build_fn=build_fn)
    watcher.start()
    watcher.stop()
    assert calls


def test_build_watcher_reports_errors(monkeypatch, tmp_path):
    root = tmp_path

    def fake_watch(*args, **kwargs):
        yield {(Change.modified, str(root / "_config.yml"))}

    monkeypatch.setattr("simiki3.watch.watch", fake_watch)

    errors = []

    def build_fn():
        raise RuntimeError("boom")

    watcher = BuildWatcher(root=root, build_fn=build_fn, on_error=errors.append)
    watcher.start()
    watcher.stop()

    assert errors and isinstance(errors[0], RuntimeError)
