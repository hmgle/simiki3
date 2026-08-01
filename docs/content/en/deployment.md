---
title: Deployment
date: 2026-08-01
category: en
lang: en
translation: /simiki3/zh/deployment.html
description: Publish a Simiki3 site with GitHub Pages or another static host.
summary: Publish a Simiki3 site with GitHub Pages or another static host.
---

# Deployment

Simiki3 produces ordinary HTML, CSS, XML, and copied assets. Any static web host can serve the generated `output/` directory.

## GitHub Pages

Build the site locally first:

```bash
uv run simiki3 build docs
```

For this repository, `.github/workflows/pages.yml` builds `docs/` on pushes to `main`, uploads `docs/output/` as a Pages artifact, and deploys it with the official GitHub Pages actions. The workflow also supports manual runs from the Actions tab.

The repository site uses:

```yaml
url: https://hmgle.github.io
root: /simiki3
```

The first Pages deployment may require the repository Pages source to be set to **GitHub Actions** in the repository settings.

## Other static hosts

Run `simiki3 build SITE`, then upload the contents of `SITE/output/`. Set `root` to the URL prefix used by the host, and preserve the same prefix in your theme links.
