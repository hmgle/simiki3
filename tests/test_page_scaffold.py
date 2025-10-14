from pathlib import Path

import pytest

from simiki3.config import default_config
from simiki3.page_scaffold import NewPageResult, PageExistsError, create_page
from simiki3.utils import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"
    assert slugify("你好 世界", default="fallback").startswith("fallback")
    assert slugify("Title!!!") == "title"


def test_create_page_writes_front_matter(tmp_path):
    config = default_config()
    result = create_page(tmp_path, config, title="Demo Page", category="intro")
    assert isinstance(result, NewPageResult)
    page_path = result.path
    assert page_path.exists()
    text = page_path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "title: \"Demo Page\"" in text
    assert "draft: true" not in text


def test_create_page_respects_draft_and_force(tmp_path):
    config = default_config()
    result = create_page(tmp_path, config, title="Draft Page", draft=True)
    assert "draft" in result.path.read_text(encoding="utf-8")

    with pytest.raises(PageExistsError):
        create_page(tmp_path, config, title="Draft Page", draft=False)

    result_force = create_page(tmp_path, config, title="Draft Page", draft=False, force=True)
    assert "draft: true" not in result_force.path.read_text(encoding="utf-8")
