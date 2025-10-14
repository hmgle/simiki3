"""Site build pipeline."""

from __future__ import annotations

import shutil
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence
import html
import xml.etree.ElementTree as ET

from .config import ConfigFiles, SiteConfig, load_config
from .content import Page, PageError, discover_markdown_files, load_page
from .theme import ThemeRenderer, ThemeError
from .utils import strip_html


@dataclass
class BuildResult:
    rendered: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    copied_assets: list[Path] = field(default_factory=list)
    generated_catalog: bool = False
    generated_feed: bool = False

    def record_rendered(self, path: Path) -> None:
        if path not in self.rendered:
            self.rendered.append(path)

    def record_skipped(self, path: Path) -> None:
        if path not in self.skipped:
            self.skipped.append(path)

    def record_asset(self, path: Path) -> None:
        if path not in self.copied_assets:
            self.copied_assets.append(path)


class SiteBuilder:
    def __init__(self, root: Path, config: SiteConfig) -> None:
        self.root = Path(root).resolve()
        self.config = config
        self.source_dir = self.root / config.source
        self.output_dir = self.root / config.destination
        self.attach_dir = self.root / config.attach
        self.theme_root = self.root / config.themes_dir / config.theme
        self.renderer = ThemeRenderer(self.theme_root)
        self._site_structure: OrderedDict[str, dict] | dict = OrderedDict()

    def build(self, *, include_drafts: bool = False) -> BuildResult:
        result = BuildResult()
        self._prepare_output()

        pages = self._load_pages()
        published_pages: list[Page] = []
        for page in pages:
            if page.meta.get("draft", False) and not include_drafts:
                result.record_skipped(page.output_relative)
                continue
            published_pages.append(page)

        self._site_structure = self._build_structure(published_pages)

        for page in published_pages:
            rendered = self._render_page(page)
            result.record_rendered(rendered)

        self._generate_catalog(published_pages, result)
        self._generate_feed(published_pages, result)

        self._copy_theme_static(result)
        self._copy_attachments(result)
        return result

    def _prepare_output(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for entry in list(self.output_dir.iterdir()):
            if entry.name in {".git", "CNAME", "favicon.ico"}:
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

    def _load_pages(self) -> list[Page]:
        if not self.source_dir.exists():
            return []
        markdown_files = discover_markdown_files(self.source_dir, config=self.config)
        pages: list[Page] = []
        for file_path in markdown_files:
            try:
                page = load_page(file_path, source_dir=self.source_dir, config=self.config)
            except PageError:
                raise
            pages.append(page)
        return pages

    def _render_page(self, page: Page) -> Path:
        return self._render_html(
            page.output_relative,
            meta=page.meta,
            html_content=page.html,
            source_path=page.source_path,
        )

    def _render_html(
        self,
        relative_output: Path,
        *,
        meta: dict,
        html_content: str,
        source_path: Path | None = None,
    ) -> Path:
        layout = meta.get("layout", "page")
        context = self._template_context(
            relative_output,
            meta=meta,
            html_content=html_content,
            source_path=source_path,
        )
        html = self.renderer.render(layout, context=context)
        destination = self.output_dir / relative_output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(html, encoding="utf-8")
        return destination.relative_to(self.output_dir)

    def _template_context(
        self,
        relative_output: Path,
        *,
        meta: dict,
        html_content: str,
        source_path: Path | None,
    ) -> dict:
        site_dict = self.config.as_dict()
        if self._site_structure:
            site_dict.update({"structure": self._site_structure})
        output_path = self.output_dir / relative_output
        permalink = self._permalink(relative_output)
        page_dict = dict(meta)
        page_dict["content"] = html_content
        page_dict["permalink"] = permalink
        page_dict["source_path"] = str(source_path) if source_path else ""
        page_dict["output_path"] = str(output_path)
        page_dict.setdefault(
            "category",
            relative_output.parent.as_posix() if relative_output.parent.parts else "",
        )
        return {
            "site": site_dict,
            "page": page_dict,
        }

    def _generate_catalog(self, pages: Sequence[Page], result: BuildResult) -> None:
        relative_output = Path("index.html")
        categories: dict[str, list[Page]] = defaultdict(list)
        for page in pages:
            category_key = (page.category or "").strip()
            categories[category_key].append(page)

        lines: list[str] = ["<h1>Pages</h1>"]
        if not pages:
            lines.append("<p>No content has been generated yet.</p>")
        else:
            for category in sorted(categories.keys()):
                display_category = category or "General"
                lines.append(f"<section class=\"catalog-category\">")
                lines.append(f"<h2>{html.escape(display_category)}</h2>")
                lines.append("<ul>")
                for page in sorted(categories[category], key=_title_sort_key):
                    permalink = self._permalink(page.output_relative)
                    title = html.escape(page.meta.get("title", page.output_relative.stem))
                    summary_text = _page_summary(page, length=140)
                    summary = html.escape(summary_text) if summary_text else ""
                    lines.append(
                        f"<li><a href=\"{permalink}\">{title}</a>"
                        + (f"<span class=\"catalog-summary\"> — {summary}</span>" if summary else "")
                        + "</li>"
                    )
                lines.append("</ul>")
                lines.append("</section>")

        html_content = "\n".join(lines)
        meta = {
            "title": self.config.title or "Home",
            "layout": "index",
            "category": "",
        }
        rendered = self._render_html(relative_output, meta=meta, html_content=html_content, source_path=None)
        result.record_rendered(rendered)
        result.generated_catalog = True

    def _generate_feed(self, pages: Sequence[Page], result: BuildResult) -> None:
        if not pages:
            return

        entries = sorted(pages, key=_page_updated, reverse=True)
        feed = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")
        site_url = self.config.url.rstrip("/") if self.config.url else ""
        feed_title = self.config.title or "Simiki3 Wiki"
        ET.SubElement(feed, "title").text = feed_title
        feed_id = site_url or self.config.root or "simiki3"
        ET.SubElement(feed, "id").text = feed_id
        ET.SubElement(feed, "updated").text = _page_updated(entries[0]).isoformat()

        if site_url:
            ET.SubElement(feed, "link", href=site_url + self.config.root)
            ET.SubElement(feed, "link", rel="self", href=f"{site_url}{self.config.root}/atom.xml".replace("//", "/"))

        for page in entries[:20]:
            entry = ET.SubElement(feed, "entry")
            ET.SubElement(entry, "title").text = page.meta.get("title", page.output_relative.stem)
            url = self._permalink(page.output_relative, absolute=True)
            ET.SubElement(entry, "id").text = url
            ET.SubElement(entry, "link", href=url)
            ET.SubElement(entry, "updated").text = _page_updated(page).isoformat()
            summary_text = page.meta.get("description") or _page_summary(page)
            summary_el = ET.SubElement(entry, "summary", type="html")
            summary_el.text = summary_text

        _indent_xml(feed)
        output = ET.tostring(feed, encoding="utf-8")
        feed_path = self.output_dir / "atom.xml"
        feed_path.parent.mkdir(parents=True, exist_ok=True)
        feed_path.write_bytes(output)
        result.generated_feed = True

    def _copy_theme_static(self, result: BuildResult) -> None:
        static_dir = self.renderer.paths.static
        if not static_dir.exists():
            return
        destination = self.output_dir / "static"
        _copytree(static_dir, destination, result)

    def _copy_attachments(self, result: BuildResult) -> None:
        if not self.attach_dir.exists():
            return
        destination = self.output_dir / self.config.attach
        _copytree(self.attach_dir, destination, result, ignore_names={".gitkeep"})

    def _build_structure(self, pages: Sequence[Page]) -> OrderedDict[str, dict]:
        root: dict[str, dict] = {}
        for page in pages:
            parts = list(page.relative_path.parts)
            current = root
            for index, part in enumerate(parts):
                if index == len(parts) - 1:
                    permalink = self._permalink(page.output_relative)
                    current[part] = _build_structure_entry(page, permalink)
                else:
                    current = current.setdefault(part, {})
        return _sort_structure(root)

    def _permalink(self, relative_output: Path, absolute: bool = False) -> str:
        root_path = f"{self.config.root}/{relative_output.as_posix()}".replace("//", "/")
        if absolute and self.config.url:
            return f"{self.config.url.rstrip('/')}{root_path}"
        return root_path


def _title_sort_key(page: Page) -> tuple[str, str]:
    title = page.meta.get("title", page.output_relative.stem)
    return (title.lower(), page.output_relative.as_posix())


def _page_updated(page: Page) -> datetime:
    value = page.meta.get("updated") or page.meta.get("date")
    return _coerce_datetime(value)


def _coerce_datetime(value) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        value = value.strip()
        value = value.replace("Z", "+00:00")
        for fmt in (None, "%Y-%m-%d %H:%M", "%Y-%m-%d"):  # try ISO first, then fallbacks
            try:
                if fmt is None:
                    dt = datetime.fromisoformat(value)
                else:
                    dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _page_summary(page: Page, *, length: int = 200) -> str:
    summary = page.meta.get("summary") or page.meta.get("description")
    if not summary:
        summary = strip_html(page.html) or page.markdown
    summary = summary.strip()
    if len(summary) > length:
        summary = summary[:length].rstrip() + "…"
    return summary


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    indent = "  "
    children = list(elem)
    if children:
        if not elem.text or not elem.text.strip():
            elem.text = "\n" + indent * (level + 1)
        for child in children:
            _indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = "\n" + indent * (level + 1)
        if not children[-1].tail or not children[-1].tail.strip():
            children[-1].tail = "\n" + indent * level
    else:
        if not elem.text or not elem.text.strip():
            elem.text = ""
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = "\n" + indent * level


def _sort_structure(structure: dict) -> OrderedDict:
    ordered = OrderedDict()
    items = []
    for key, value in structure.items():
        if isinstance(value, dict) and "title" in value:
            sort_key = value.get("title", key).lower()
        else:
            sort_key = key.lower()
        items.append((key, value, sort_key))

    for key, value, _ in sorted(items, key=lambda item: item[2]):
        if isinstance(value, dict) and "title" not in value:
            value = _sort_structure(value)
        ordered[key] = value
    return ordered


def _build_structure_entry(page: Page, permalink: str) -> dict:
    entry = {
        "title": page.meta.get("title", page.output_relative.stem),
        "name": page.output_relative.stem,
        "permalink": permalink,
    }
    for key in ("date", "updated", "tags", "category"):
        if key in page.meta:
            entry[key] = page.meta[key]
    return entry


def build_site(
    root: Path,
    *,
    include_drafts: bool = False,
    config: SiteConfig | None = None,
) -> BuildResult:
    root = Path(root)
    if config is None:
        config_path = ConfigFiles().resolve(root)
        config = load_config(config_path)
    builder = SiteBuilder(root, config)
    return builder.build(include_drafts=include_drafts)


def _copytree(src: Path, dst: Path, result: BuildResult, ignore_names: Iterable[str] | None = None) -> None:
    src = Path(src)
    if not src.exists():
        return
    dst = Path(dst)
    ignore = set(ignore_names or [])
    for item in src.rglob("*"):
        relative = item.relative_to(src)
        if any(part.startswith('.') for part in relative.parts):
            continue
        if item.name in ignore:
            continue
        destination = dst / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)
            result.record_asset(destination.relative_to(dst))
