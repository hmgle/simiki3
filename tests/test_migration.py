from pathlib import Path

import pytest
import shutil

from simiki3.config import default_config
from simiki3.migration import analyse_site, apply_fixes
from simiki3.page_scaffold import create_page
from simiki3.scaffold import initialise_site


def test_analyse_site_detects_legacy_layout(tmp_path):
    root = tmp_path / "site"
    initialise_site(root)
    config = default_config()

    page_path = root / config.source / "intro" / "legacy.md"
    page_path.write_text(
        """---
title: Legacy Layout
layout: post
date: 2020-01-01
---

Content
""",
        encoding="utf-8",
    )

    report = analyse_site(root, config)
    assert report.page_issues
    assert any("legacy layout" in issue.message for issue in report.page_issues)


def test_analyse_site_warns_missing_date(tmp_path):
    root = tmp_path / "site"
    initialise_site(root)
    config = default_config()

    create_page(root, config, title="No Date", category="intro", slug="no-date", draft=False, force=True)
    page_path = root / config.source / "intro" / "no-date.md"
    text = page_path.read_text(encoding="utf-8")
    # remove date line to trigger warning
    lines = [line for line in text.splitlines() if not line.startswith("date:")]
    page_path.write_text("\n".join(lines), encoding="utf-8")

    report = analyse_site(root, config)
    assert any("missing date" in issue.message for issue in report.page_issues)

def test_apply_fixes_updates_layout_and_date(tmp_path):
    root = tmp_path / "site"
    initialise_site(root)
    config = default_config()

    page = root / config.source / "intro" / "legacy.md"
    page.write_text(
        """---
title: Legacy Layout
layout: post
---

Legacy content
""",
        encoding="utf-8",
    )

    summary = analyse_site(root, config)
    assert summary.page_issues

    apply_fixes(root, config, fix_config_file=False, fix_pages=True, sync_theme=False, dry_run=False)
    text = page.read_text(encoding="utf-8")
    assert "layout: page" in text
    assert "date:" in text

def test_apply_fixes_syncs_theme(tmp_path):
    root = tmp_path / "site"
    initialise_site(root)
    config = default_config()

    theme_dir = root / config.themes_dir / config.theme
    if theme_dir.exists():
        shutil.rmtree(theme_dir)

    summary = apply_fixes(root, config, sync_theme=True, backup=False, dry_run=False)
    assert summary.theme_synced is True
    assert theme_dir.exists()
