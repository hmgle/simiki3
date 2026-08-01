from pathlib import Path

from simiki3.validate import compare_directories
import pytest


def test_compare_directories_detects_changes(tmp_path):
    legacy = tmp_path / 'legacy'
    new = tmp_path / 'new'
    (legacy / 'sub').mkdir(parents=True)
    (new / 'sub').mkdir(parents=True)

    (legacy / 'index.html').write_text('<h1>Legacy</h1>', encoding='utf-8')
    (new / 'index.html').write_text('<h1>Legacy</h1>', encoding='utf-8')

    (legacy / 'sub' / 'page.html').write_text('<p>old</p>', encoding='utf-8')
    (new / 'sub' / 'page.html').write_text('<p>new</p>', encoding='utf-8')

    (legacy / 'only-legacy.html').write_text('legacy only', encoding='utf-8')
    (new / 'only-new.html').write_text('new only', encoding='utf-8')

    result = compare_directories(legacy, new, extensions=['html'])
    assert Path('only-legacy.html') in result.missing_in_new
    assert Path('only-new.html') in result.missing_in_legacy
    assert Path('sub/page.html') in result.changed_files
    assert not result.is_clean


def test_compare_directories_rejects_missing_roots(tmp_path):
    with pytest.raises(FileNotFoundError):
        compare_directories(tmp_path / "legacy", tmp_path / "new")
