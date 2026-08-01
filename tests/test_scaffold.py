from pathlib import Path

import pytest
import yaml

from simiki3.config import default_config
from simiki3.scaffold import initialise_site


def test_initialise_site_creates_expected_structure(tmp_path):
    target = tmp_path / "wiki"
    config = default_config().with_overrides(title="Docs", root="/docs")

    result = initialise_site(target, config=config)

    assert (target / "_config.yml").exists()
    assert (target / "content" / "intro" / "welcome.md").exists()
    assert (target / config.themes_dir / config.theme / "templates" / "page.html").exists()
    assert (target / "attach" / ".gitkeep").exists()
    assert (target / "output").is_dir()

    with (target / "_config.yml").open() as fh:
        loaded = yaml.safe_load(fh)
    assert loaded["title"] == "Docs"
    assert loaded["root"] == "/docs"

    assert "content/intro" in result.created_dirs
    assert f"{config.themes_dir}/{config.theme}/templates/page.html" in result.created_files
    assert not result.skipped


def test_initialise_site_refuses_to_overwrite(tmp_path):
    target = tmp_path / "wiki"
    target.mkdir()
    (target / "_config.yml").write_text("title: existing\n")

    with pytest.raises(FileExistsError):
        initialise_site(target)


def test_initialise_site_force_overwrites(tmp_path):
    target = tmp_path / "wiki"
    target.mkdir()
    (target / "_config.yml").write_text("title: existing\n")

    result = initialise_site(target, force=True)
    assert "_config.yml" in result.created_files
    with (target / "_config.yml").open() as fh:
        data = yaml.safe_load(fh)
    assert data["title"] == "Simiki Wiki"


def test_initialise_site_raises_for_non_directory(tmp_path):
    target = tmp_path / "notadir"
    target.write_text("file")
    with pytest.raises(NotADirectoryError):
        initialise_site(target)
