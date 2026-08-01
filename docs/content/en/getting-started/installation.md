---
title: Installation
date: 2026-08-01
category: en/getting-started
lang: en
translation: /simiki3/zh/getting-started/installation.html
description: Install Simiki3 and prepare a local development environment.
summary: Install Simiki3 and prepare a local development environment.
---

# Installation

Simiki3 requires Python 3.10 or newer.

## From a source checkout

The repository uses [uv](https://docs.astral.sh/uv/) for reproducible development environments:

```bash
git clone https://github.com/hmgle/simiki3.git
cd simiki3
uv sync --extra dev
uv run simiki3 --version
```

The `dev` extra installs the test and lint tools used by the project.

## As an installed command

When using a released package, install `simiki3` with your preferred Python package manager and make sure the resulting `simiki3` command is on your `PATH`. Verify the installation with:

```bash
simiki3 --version
```

## Next step

Continue with the [quick start](/simiki3/en/getting-started/quick-start.html) to initialize a site and render your first page.
