from pathlib import Path

import pytest

from simiki3.config import (
    ConfigError,
    ConfigFiles,
    SiteConfig,
    default_config,
    load_config,
    load_legacy_config,
)


def test_default_config_normalises_values():
    config = default_config()
    assert config.root == "/"
    assert config.default_ext == "md"
    assert config.themes_dir == "themes"


def test_load_config_merges_defaults(tmp_path):
    cfg = tmp_path / "_config.yml"
    cfg.write_text(
        """
url: https://example.com/wiki/
root: /docs/
theme: modern
pygments: false
        """.strip()
    )

    config = load_config(cfg)
    assert config.url == "https://example.com/wiki"
    assert config.root == "/docs"
    assert config.theme == "modern"
    assert config.pygments is False
    # defaulted value retained
    assert config.source == "content"


def test_load_config_accepts_empty_legacy_text_fields(tmp_path):
    cfg = tmp_path / "_config.yml"
    cfg.write_text(
        "url:\n"
        "keywords:\n"
        "description:\n"
        "author:\n"
        "root: /wiki/\n",
        encoding="utf-8",
    )

    config = load_config(cfg)

    assert config.url == ""
    assert config.keywords == ""
    assert config.description == ""
    assert config.author == ""
    assert config.root == "/wiki"


def test_load_config_accepts_overrides(tmp_path):
    cfg = tmp_path / "_config.yml"
    cfg.write_text("title: Legacy\n")

    config = load_config(cfg, overrides={"title": "Overridden", "debug": True})
    assert config.title == "Overridden"
    assert config.debug is True


def test_config_overrides_are_validated():
    config = default_config().with_overrides(url="https://example.com/", root="/docs/")

    assert config.url == "https://example.com"
    assert config.root == "/docs"

    with pytest.raises(ConfigError):
        default_config().with_overrides(root="docs")


@pytest.mark.parametrize(
    "field, value",
    [
        ("source", "../content"),
        ("destination", "content"),
        ("themes_dir", "/tmp/themes"),
        ("default_ext", "../html"),
    ],
)
def test_config_rejects_unsafe_or_colliding_paths(field, value):
    with pytest.raises((ConfigError, ValueError)):
        if field == "default_ext":
            SiteConfig(**{field: value})
        else:
            default_config().with_overrides(**{field: value})


def test_load_legacy_config_normalises_old_fields(tmp_path):
    config_path = tmp_path / "_config.yml"
    config_path.write_text(
        "root: docs\n"
        "theme: /simple2/\n"
        "deploy:\n"
        "  - type: git\n",
        encoding="utf-8",
    )

    config = load_legacy_config(config_path)

    assert config.root == "/docs"
    assert config.theme == "simple2"


def test_missing_config_file_raises(tmp_path):
    missing = tmp_path / "_config.yml"
    with pytest.raises(FileNotFoundError):
        load_config(missing)


def test_invalid_root_raises(tmp_path):
    cfg = tmp_path / "_config.yml"
    cfg.write_text("root: docs\n")

    with pytest.raises(ConfigError) as excinfo:
        load_config(cfg)
    assert "root" in str(excinfo.value.validation_error)


def test_non_mapping_yaml_raises(tmp_path):
    cfg = tmp_path / "_config.yml"
    cfg.write_text("- 1\n- 2\n")

    with pytest.raises(ConfigError):
        load_config(cfg)


def test_config_files_resolve(tmp_path):
    config_files = ConfigFiles()
    resolved = config_files.resolve(tmp_path)
    assert resolved == tmp_path / "_config.yml"
