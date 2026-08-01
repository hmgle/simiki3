---
title: Quick start
date: 2026-08-01
category: en/getting-started
lang: en
translation: /simiki3/zh/getting-started/quick-start.html
description: Create, build, and preview a Simiki3 site in a few commands.
summary: Create, build, and preview a Simiki3 site in a few commands.
---

# Quick start

Create a new site, add a page, build it, and start the local preview server:

```bash
simiki3 init my-wiki
simiki3 new "First page" --path my-wiki --category intro
simiki3 build my-wiki
simiki3 serve my-wiki --watch
```

The generated site has this layout:

```text
my-wiki/
├── _config.yml
├── attach/
├── content/
│   └── intro/
├── output/
└── themes/
    └── simple2/
```

Write Markdown source files under `content/`. Simiki3 writes the generated HTML, CSS, feed, and copied attachments under `output/`.

## Create a page manually

Every page can begin with YAML front matter:

```markdown
---
title: Project notes
date: 2026-08-01
category: notes
---

# Project notes

Markdown content goes here.
```

The file extension defaults to `.md`. Use the [configuration reference](/simiki3/en/reference/configuration.html) to change the source or output directories.
