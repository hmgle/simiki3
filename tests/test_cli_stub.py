from pathlib import Path
import shutil
import yaml

from typer.testing import CliRunner

from simiki3.cli import app


def test_version_flag_displays_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "simiki3" in result.stdout


def test_goals_command_outputs_table():
    runner = CliRunner()
    result = runner.invoke(app, ["goals"])
    assert result.exit_code == 0
    assert "Roadmap" in result.stdout
    assert "CLI & packaging" in result.stdout


def test_init_creates_project_structure():
    runner = CliRunner()
    with runner.isolated_filesystem():
        target = Path("site")
        result = runner.invoke(app, ["init", str(target)])
        assert result.exit_code == 0
        output = result.stdout
        assert "Initialized wiki" in output
        assert (target / "_config.yml").exists()
        assert (target / "content" / "intro" / "welcome.md").exists()
        assert (target / "themes" / "simple2" / "templates" / "page.html").exists()


def test_init_refuses_to_overwrite_without_force(tmp_path):
    runner = CliRunner()
    site = tmp_path / "site"
    site.mkdir()
    (site / "_config.yml").write_text("title: existing\n")

    result = runner.invoke(app, ["init", str(site)])
    assert result.exit_code == 1
    assert "Refusing to overwrite" in result.stdout


def test_build_command_produces_html(tmp_path):
    runner = CliRunner()
    site = tmp_path / "site"
    init_result = runner.invoke(app, ["init", str(site)])
    assert init_result.exit_code == 0

    build_result = runner.invoke(app, ["build", str(site)])
    assert build_result.exit_code == 0
    assert "Build complete" in build_result.stdout
    assert (site / "output" / "intro" / "welcome.html").exists()
    assert (site / "output" / "atom.xml").exists()


def test_new_command_creates_page(tmp_path):
    runner = CliRunner()
    site = tmp_path / "site"
    init_result = runner.invoke(app, ["init", str(site)])
    assert init_result.exit_code == 0

    new_result = runner.invoke(
        app,
        [
            "new",
            "My New Page",
            "--path",
            str(site),
            "--category",
            "notes",
        ],
    )
    assert new_result.exit_code == 0
    assert "Created" in new_result.stdout
    output_file = site / "content" / "notes" / "my-new-page.md"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert yaml.safe_load(content.split("---", 2)[1])["title"] == "My New Page"


def test_theme_list_command(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["theme", "list"])
    assert result.exit_code == 0
    assert "default" in result.stdout
    assert "simple" in result.stdout


def test_theme_sync_command(tmp_path):
    runner = CliRunner()
    site = tmp_path / "site"
    init_result = runner.invoke(app, ["init", str(site)])
    assert init_result.exit_code == 0

    theme_path = site / "themes" / "default"
    if theme_path.exists():
        shutil.rmtree(theme_path)

    sync_result = runner.invoke(app, ["theme", "sync", "default", "--path", str(site)])
    assert sync_result.exit_code == 0
    assert (site / "themes" / "default" / "templates" / "page.html").exists()

def test_migrate_audit_detects_blockers(tmp_path):
    runner = CliRunner()
    site = tmp_path / "legacy"
    runner.invoke(app, ["init", str(site)])

    legacy_page = site / "content" / "intro" / "legacy.md"
    legacy_page.write_text(
        """---
title: Legacy Layout
layout: post
---

Legacy content
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["migrate", "audit", str(site)])
    assert result.exit_code == 1
    assert "legacy layout" in result.stdout


def test_migrate_audit_passes_when_clean(tmp_path):
    runner = CliRunner()
    site = tmp_path / "clean"
    runner.invoke(app, ["init", str(site)])

    welcome = site / "content" / "intro" / "welcome.md"
    text = welcome.read_text(encoding="utf-8")
    if "date:" not in text:
        welcome.write_text(text.replace("---\n", "---\ndate: 2024-01-01\n"), encoding="utf-8")

    result = runner.invoke(app, ["migrate", "audit", str(site)])
    assert result.exit_code == 0
    assert "ready" in result.stdout.lower()

def test_migrate_fix_updates_files(tmp_path):
    runner = CliRunner()
    site = tmp_path / "fix"
    runner.invoke(app, ["init", str(site)])

    # tweak config to include trailing slash and missing leading slash
    config_path = site / "_config.yml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg["url"] = "https://example.com/wiki/"
    cfg["root"] = "docs"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    page = site / "content" / "intro" / "legacy.md"
    page.write_text(
        """---
title: Legacy Layout
layout: post
---

Legacy content
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["migrate", "fix", str(site)])
    assert result.exit_code == 0
    fixed_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert fixed_config["url"] == "https://example.com/wiki"
    assert fixed_config["root"] == "/docs"

    text = page.read_text(encoding="utf-8")
    assert "layout: page" in text
    assert "date:" in text
    assert (site / "_config.yml.bak").exists()
    assert any(p.name.startswith("legacy.md.bak") for p in page.parent.glob("legacy.md.bak*"))
    assert "Theme assets already present" in result.stdout


def test_migrate_fix_dry_run(tmp_path):
    runner = CliRunner()
    site = tmp_path / "dry"
    runner.invoke(app, ["init", str(site)])

    page = site / "content" / "intro" / "legacy.md"
    original = """---
title: Legacy Layout
layout: post
---

Legacy content
"""
    page.write_text(original, encoding="utf-8")

    config_path = site / "_config.yml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg["url"] = "https://example.com/wiki/"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    result = runner.invoke(app, ["migrate", "fix", str(site), "--dry-run"])
    assert result.exit_code == 0
    assert page.read_text(encoding="utf-8") == original
    cfg_after = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg_after["url"] == "https://example.com/wiki/"
    assert not any(p.suffix.endswith('.bak') for p in page.parent.glob('legacy.md.bak*'))
    assert not (site / "_config.yml.bak").exists()
    assert "Dry run" in result.stdout
    assert "Theme assets already present" in result.stdout

def test_migrate_fix_syncs_missing_theme(tmp_path):
    runner = CliRunner()
    site = tmp_path / "theme-site"
    runner.invoke(app, ["init", str(site)])

    theme_dir = site / "themes" / "simple2"
    if theme_dir.exists():
        shutil.rmtree(theme_dir)

    result = runner.invoke(app, ["migrate", "fix", str(site)])
    assert result.exit_code == 0
    assert theme_dir.exists()
    assert "synced theme" in result.stdout.lower()

def test_migrate_fix_without_backup(tmp_path):
    runner = CliRunner()
    site = tmp_path / "nobackup"
    runner.invoke(app, ["init", str(site)])

    config_path = site / "_config.yml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg["url"] = "https://example.com/wiki/"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    page = site / "content" / "intro" / "legacy.md"
    page.write_text(
        """---
title: Legacy Layout
layout: post
---

Legacy content
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["migrate", "fix", str(site), "--no-backup"])
    assert result.exit_code == 0
    assert not list(page.parent.glob("legacy.md.bak*"))
    assert not (site / "_config.yml.bak").exists()


def test_update_command_syncs_files(tmp_path):
    runner = CliRunner()
    site = tmp_path / 'site'
    runner.invoke(app, ['init', str(site)])

    config_in = site / '_config.yml.in'
    if config_in.exists():
        config_in.unlink()

    result = runner.invoke(app, ['update', str(site), '--overwrite', '--examples'])
    assert result.exit_code == 0
    assert (site / '_config.yml.in').exists()
    assert 'Copied files' in result.stdout



def test_validate_command_flags_differences(tmp_path):
    runner = CliRunner()
    legacy = tmp_path / 'legacy'
    new = tmp_path / 'new'
    legacy.mkdir()
    new.mkdir()
    (legacy / 'index.html').write_text('<h1>Legacy</h1>', encoding='utf-8')
    (new / 'index.html').write_text('<h1>Modified</h1>', encoding='utf-8')

    result = runner.invoke(app, ['validate', str(legacy), str(new)])
    assert result.exit_code == 1
    assert 'Changed files' in result.stdout
