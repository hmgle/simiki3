---
title: CLI reference
date: 2026-08-01
category: en/reference
lang: en
translation: /simiki3/zh/reference/cli.html
description: Reference for the Simiki3 command-line interface.
summary: Reference for the Simiki3 command-line interface.
---

# CLI reference

Run `simiki3 --help` for command-specific help. The main commands are:

| Command | Purpose |
| --- | --- |
| `simiki3 init [PATH]` | Create a site skeleton with configuration, content, output, and a theme. |
| `simiki3 new TITLE --path PATH` | Create a Markdown page with front matter. |
| `simiki3 build [PATH]` | Render published Markdown pages into static HTML. |
| `simiki3 serve [PATH] --watch` | Build and serve the output directory locally, rebuilding on changes. |
| `simiki3 update [PATH]` | Refresh bundled configuration templates and theme assets. |
| `simiki3 theme list` | List themes bundled with Simiki3. |
| `simiki3 theme sync THEME --path PATH` | Copy a bundled theme into an existing site. |
| `simiki3 validate LEGACY NEW` | Compare selected files in two build directories. |
| `simiki3 migrate audit PATH` | Inspect a legacy site and report migration blockers. |
| `simiki3 migrate fix PATH` | Apply safe migration fixes, optionally as a dry run. |
| `simiki3 goals` | Show the current project roadmap. |

## Build options

Use `--include-drafts` to include pages whose front matter contains `draft: true`:

```bash
simiki3 build my-wiki --include-drafts
```

Use `--watch` with `build` when you want the build command itself to monitor source files. The `serve --watch` workflow is usually more convenient for browser preview.

## Migration options

Always audit a legacy site first:

```bash
simiki3 migrate audit legacy-site
simiki3 migrate fix legacy-site --dry-run
simiki3 migrate fix legacy-site
```

Migration fixes create backups by default. Review them before removing the legacy files.
