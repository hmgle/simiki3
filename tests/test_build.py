from pathlib import Path

import pytest
import yaml

from simiki3.build import BuildResult, build_site
from simiki3.scaffold import initialise_site


def test_build_site_renders_markdown(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)

    result = build_site(site_root)

    output_file = site_root / "output" / "intro" / "welcome.html"
    assert output_file.exists()
    html = output_file.read_text(encoding="utf-8")
    assert "Hello, Simiki3" in html
    assert isinstance(result, BuildResult)
    assert result.rendered
    catalog = site_root / "output" / "index.html"
    assert catalog.exists()
    catalog_html = catalog.read_text(encoding="utf-8")
    assert "Pages" in catalog_html


def test_build_site_skips_draft(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)

    draft_file = site_root / "content" / "intro" / "draft.md"
    draft_file.write_text(
        """
---
title: Draft Page
draft: true
---

Draft content
        """.strip()
    )

    result = build_site(site_root)
    assert any(path == Path("intro/draft.html") for path in result.skipped)
    assert not (site_root / "output" / "intro" / "draft.html").exists()

    result_with_drafts = build_site(site_root, include_drafts=True)
    assert any(path == Path("intro/draft.html") for path in result_with_drafts.rendered)
    assert (site_root / "output" / "intro" / "draft.html").exists()


def test_build_site_copies_attachments(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)
    attachment = site_root / "attach" / "images"
    attachment.mkdir(parents=True, exist_ok=True)
    (attachment / "example.txt").write_text("hello", encoding="utf-8")

    build_site(site_root)

    assert (site_root / "output" / "attach" / "images" / "example.txt").exists()


def test_build_site_generates_feed(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)

    config_path = site_root / "_config.yml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["url"] = "https://example.com"
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    build_site(site_root)

    feed_file = site_root / "output" / "atom.xml"
    assert feed_file.exists()
    feed_xml = feed_file.read_text(encoding="utf-8")
    assert "<feed" in feed_xml
    assert "https://example.com" in feed_xml
