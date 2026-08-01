---
title: Migration
date: 2026-08-01
category: en/guides
lang: en
translation: /simiki3/zh/guides/migration.html
description: Audit and migrate a legacy Simiki site to Simiki3.
summary: Audit and migrate a legacy Simiki site to Simiki3.
---

# Migration

Simiki3 includes migration helpers for common legacy Simiki layouts. The migration flow is deliberately inspectable: audit first, preview fixes, then apply them with backups.

## Audit a site

```bash
simiki3 migrate audit legacy-site
```

The audit checks configuration normalization, legacy `layout: post` values, missing page dates, page parsing errors, and missing bundled theme assets.

## Preview and apply fixes

```bash
simiki3 migrate fix legacy-site --dry-run
simiki3 migrate fix legacy-site
```

By default, fixes normalize the configuration, update page front matter, synchronize a bundled theme when available, and create `.bak` backups before changing files.

## Review the result

Build the migrated site and compare it with the old build when both directories are available:

```bash
simiki3 build legacy-site
simiki3 validate old-output legacy-site/output
```

Migration does not automatically rewrite arbitrary links or port custom legacy themes. Review those parts manually.
