---
title: Themes
date: 2026-08-01
category: en/guides
lang: en
translation: /simiki3/zh/guides/themes.html
description: Select, synchronize, and customize a Simiki3 theme.
summary: Select, synchronize, and customize a Simiki3 theme.
---

# Themes

Simiki3 renders pages through the theme selected in `_config.yml`. New sites receive the configured bundled theme under `themes/`.

## List and synchronize bundled themes

```bash
simiki3 theme list
simiki3 theme sync default --path my-wiki
```

Use `--force` with `theme sync` only when you intend to overwrite local theme files.

## Theme layout

A theme contains Jinja templates and optional static assets:

```text
themes/my-theme/
├── static/
│   └── css/
└── templates/
    ├── base.html
    ├── index.html
    └── page.html
```

`page.html` is required. `index.html` controls the generated catalog page, and `base.html` can provide shared HTML structure for themes that extend it.

## Template context

Templates receive `site`, `page`, `pages`, and `default_home_page`. Site metadata is available through `site`; rendered Markdown is available as `page.content`. Use the `safe` filter for that already-rendered HTML.

The build copies theme files under `static/` to the generated site's `static/` directory. Keep links root-aware by prefixing them with `site.root_url` when the site may be deployed below a domain root.
