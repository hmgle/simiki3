from pathlib import Path

from simiki3.config import default_config
from simiki3.update_site import update_site
from simiki3.scaffold import initialise_site


def test_update_site_copies_templates(tmp_path):
    root = tmp_path / 'wiki'
    initialise_site(root)
    result = update_site(root, overwrite=True, include_examples=True, sync_theme=True)

    assert (root / '_config.yml.in').exists()
    assert (root / 'fabfile.py').exists()
    assert (root / 'Dockerfile').exists()
    assert (root / 'content' / 'gettingstarted.md').exists()
    assert result.theme_synced


def test_update_site_respects_overwrite(tmp_path):
    root = tmp_path / 'wiki'
    initialise_site(root)
    (root / '_config.yml.in').write_text('custom', encoding='utf-8')

    result_skipped = update_site(root, overwrite=False)
    assert '_config.yml.in' in [str(p) for p in result_skipped.skipped_files]

    result_overwrite = update_site(root, overwrite=True)
    assert '_config.yml.in' in [str(p) for p in result_overwrite.copied_files]


if __name__ == '__main__':
    pass
