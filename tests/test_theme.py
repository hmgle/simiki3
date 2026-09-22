import re
from importlib import resources
from pathlib import Path

import pytest

from simiki3.config import default_config
from simiki3.theme import THEME_PACKAGE, ThemeError, builtin_themes, sync_theme_to_site


def test_builtin_themes_contains_default():
    assert "default" in builtin_themes()


def test_sync_theme_to_site(tmp_path):
    config = default_config()
    result = sync_theme_to_site(tmp_path, config, "default")
    assert result.created
    page_template = tmp_path / config.themes_dir / "default" / "templates" / "page.html"
    assert page_template.exists()

    # second run without force should skip files
    result2 = sync_theme_to_site(tmp_path, config, "default", force=False)
    assert result2.skipped

    # with force we should report overwrites
    result3 = sync_theme_to_site(tmp_path, config, "default", force=True)
    assert result3.overwritten


def test_sync_theme_unknown(tmp_path):
    with pytest.raises(ThemeError):
        sync_theme_to_site(tmp_path, default_config(), "missing-theme")


def _theme_css(theme: str) -> str:
    css = resources.files(THEME_PACKAGE) / theme / "static" / "css" / "style.css"
    with resources.as_file(css) as css_path:
        return css_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ["simple", "simple2"])
def test_theme_toc_uses_scrollbar_safe_fixed_sidebar(theme):
    """Long TOCs remain visible without overlapping the article."""
    css = _theme_css(theme)
    toc_rules = re.findall(r"\.toc\s*\{[^}]*\}", css)
    assert toc_rules
    assert all("float" not in rule for rule in toc_rules)
    assert all("position: absolute" not in rule for rule in toc_rules)
    assert any("position: fixed" in rule for rule in toc_rules)
    assert all("100vw" not in rule for rule in toc_rules)
    assert any("left: calc(50% + 380px + 1em)" in rule for rule in toc_rules)
    container_rules = re.findall(r"#container\s*\{[^}]*\}", css)
    assert any("position: relative" in rule for rule in container_rules)
    assert "max-height" in css
