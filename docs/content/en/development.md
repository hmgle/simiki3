---
title: Development
date: 2026-08-01
category: en
lang: en
translation: /simiki3/zh/development.html
description: Run the Simiki3 development workflow and test suite.
summary: Run the Simiki3 development workflow and test suite.
---

# Development

Simiki3 targets Python 3.10 and newer. The repository uses `uv` to manage dependencies and `pytest` and `ruff` for validation.

## Set up

```bash
git clone https://github.com/hmgle/simiki3.git
cd simiki3
uv sync --extra dev
```

## Validate changes

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
uv run --extra dev python -m compileall -q src tests
```

The end-to-end smoke path is `init → build → serve`. Changes to themes and migration behavior should include integration coverage.

## Build these docs locally

The repository documentation is itself a Simiki3 site:

```bash
uv run simiki3 build docs
uv run simiki3 serve docs --watch
```

Generated files are written to `docs/output/` and are intentionally ignored by Git.
