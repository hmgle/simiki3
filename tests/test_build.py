from pathlib import Path

import pytest
import yaml

from simiki3.build import BuildResult, build_site
from simiki3.config import default_config
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
    assert "Welcome to Simiki Wiki" in catalog_html


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


def test_catalog_uses_explicit_summaries_and_separates_them_from_titles(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)

    page_path = site_root / "content" / "intro" / "catalog-page.md"
    page_path.write_text(
        """
---
title: Catalog Page
summary: A concise catalog summary.
---

# Body heading

This body text must stay out of the catalog.
        """.strip(),
        encoding="utf-8",
    )

    build_site(site_root)

    catalog_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    assert (
        '<li class="catalog-page">\n'
        '  <a class="catalog-title" href="/intro/catalog-page.html">Catalog Page</a>\n'
        '  <div class="catalog-summary">A concise catalog summary.</div>\n'
        "</li>"
    ) in catalog_html
    assert "Body heading" not in catalog_html
    assert "This body text must stay out of the catalog." not in catalog_html


def test_catalog_omits_summary_when_page_has_no_summary_metadata(tmp_path):
    site_root = tmp_path / "site"
    initialise_site(site_root)

    page_path = site_root / "content" / "intro" / "title-only.md"
    page_path.write_text(
        """
---
title: Title Only
---

The page body is not a catalog summary.
        """.strip(),
        encoding="utf-8",
    )

    build_site(site_root)

    catalog_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    assert (
        '<li class="catalog-page">\n'
        '  <a class="catalog-title" href="/intro/title-only.html">Title Only</a>\n'
        "</li>"
    ) in catalog_html
    assert "The page body is not a catalog summary." not in catalog_html


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


def test_build_site_supports_configured_legacy_theme_and_root(tmp_path):
    site_root = tmp_path / "site"
    config = default_config().with_overrides(
        theme="simple", root="/docs", url="https://example.com/wiki"
    )
    initialise_site(site_root, config=config)

    build_site(site_root, config=config)

    page_html = (site_root / "output" / "intro" / "welcome.html").read_text(encoding="utf-8")
    index_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    feed_xml = (site_root / "output" / "atom.xml").read_text(encoding="utf-8")
    assert "/docs/static/css/style.css" in page_html
    assert "Pages" in index_html
    assert "https://example.com/wiki/docs/atom.xml" in feed_xml
    assert "https:/example.com" not in feed_xml


@pytest.mark.parametrize("theme", ["default", "simple", "simple2"])
def test_build_site_does_not_escape_rendered_html(tmp_path, theme):
    """Rendered Markdown must reach the page as HTML, not escaped text."""
    site_root = tmp_path / "site"
    config = default_config().with_overrides(theme=theme)
    initialise_site(site_root, config=config)

    build_site(site_root, config=config)

    page_html = (site_root / "output" / "intro" / "welcome.html").read_text(encoding="utf-8")
    index_html = (site_root / "output" / "index.html").read_text(encoding="utf-8")
    assert "<h1" in page_html
    assert "&lt;h1" not in page_html
    assert "<h1>Pages</h1>" in index_html
    assert "&lt;h1" not in index_html
