# Simiki3

Simiki3 is a Python 3.10+ static wiki generator inspired by [Simiki](https://github.com/tankywoo/simiki). It converts Markdown pages with YAML front matter into a static site, including a catalog, Atom feed, theme assets, and attachments.

Read the [Simiki3 documentation](https://hmgle.github.io/simiki3/) for the full bilingual guide.

## Install

For development:

```bash
uv sync --extra dev
```

For a regular installation:

```bash
python -m pip install simiki3
```

The command-line entry point is `simiki3`.

## Quick start

```bash
simiki3 init my-wiki
simiki3 new "First page" --path my-wiki --category intro
simiki3 build my-wiki
simiki3 serve my-wiki --watch
```

The generated site uses `content/` for Markdown sources and `output/` for generated files. The default bundled theme is `simple2`; the configured theme is copied into the site during initialization.

Each build cleans the configured destination before rendering, while preserving `CNAME` and `favicon.ico`. Keep source files and manually maintained deployment files outside the generated destination unless they are explicitly preserved.

## Common commands

```text
simiki3 init [PATH]                  Create a site skeleton
simiki3 new TITLE --path PATH        Create a Markdown page
simiki3 build [PATH]                 Render the site
simiki3 serve [PATH]                 Build and serve locally
simiki3 update [PATH]                Refresh bundled templates and assets
simiki3 theme list                   List bundled themes
simiki3 theme sync THEME --path PATH Copy a theme into a site
simiki3 validate LEGACY NEW          Compare two build outputs
simiki3 migrate audit PATH           Inspect a legacy site
simiki3 migrate fix PATH             Apply safe migration fixes
```

Use `simiki3 build --include-drafts` to render pages whose front matter contains `draft: true`. `simiki3 serve --watch` rebuilds when source files change.

## Configuration

The configuration file is `_config.yml`. Important fields are:

- `source`: Markdown source directory, default `content`
- `destination`: generated site directory, default `output`
- `attach`: attachment directory, default `attach`
- `themes_dir`: installed theme directory, default `themes`
- `theme`: configured bundled or site-local theme, default `simple2`
- `root`: URL prefix such as `/docs`
- `url`: public site URL used by the Atom feed

Source and output directories must remain relative to the site root and must not contain `..` path traversal components.

## Migration

Migration support currently normalizes common legacy configuration values, detects legacy `layout: post`, adds missing page dates, and synchronizes bundled theme assets. It does not automatically rewrite arbitrary links or port custom legacy themes. Run the audit first and review backups before applying fixes:

```bash
simiki3 migrate audit legacy-site
simiki3 migrate fix legacy-site --dry-run
simiki3 migrate fix legacy-site
```

The optional `--examples` update copies the getting-started page into the configured source directory. The bundled Fabric deployment helper remains a legacy compatibility asset and requires its own compatible Fabric installation.

## Development

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
uv run --extra dev python -m compileall -q src tests
```

The project is pre-alpha. The end-to-end smoke path is `init → build → serve`; theme and migration changes should be covered by integration tests before release.

## Roadmap

Run `simiki3 goals` for the live version of this table.

| Milestone | Status |
| --- | --- |
| CLI & packaging | Implemented: init/new/build/theme/update/validate/serve/migrate |
| Site initialization | Implemented: project generator and bundled themes |
| Content pipeline | Implemented: Markdown, catalog, Atom feed, attachments |
| Preview & watch | Implemented: local server with incremental rebuilds |
| Deployment helpers | Planned: port rsync/git/FTP deploy support from Simiki |
| Release hardening | Planned: CI, documentation, first release |
