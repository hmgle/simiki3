---
title: Configuration
date: 2026-08-01
category: en/reference
lang: en
translation: /simiki3/zh/reference/configuration.html
description: Configure site metadata, paths, URL prefixes, and themes.
summary: Configure site metadata, paths, URL prefixes, and themes.
---

# Configuration

Simiki3 reads `_config.yml` from the site root. A minimal configuration looks like this:

```yaml
title: My Wiki
description: Notes and documentation
author: Your Name
url: https://example.com
root: /wiki
source: content
destination: output
theme: simple2
```

## Main fields

| Field | Default | Description |
| --- | --- | --- |
| `url` | empty | Public site URL used for absolute Atom feed links. |
| `title` | `Simiki Wiki` | Site title shown by themes. |
| `keywords` | empty | Comma-separated metadata keywords. |
| `description` | empty | Site description used in metadata and themes. |
| `author` | empty | Author shown in the site footer. |
| `root` | `/` | URL prefix for a project site, such as `/simiki3`. |
| `source` | `content` | Markdown source directory relative to the site root. |
| `destination` | `output` | Generated site directory relative to the site root. |
| `attach` | `attach` | Attachment directory copied into the output. |
| `themes_dir` | `themes` | Installed theme directory. |
| `theme` | `simple2` | Theme selected for rendering. |
| `default_ext` | `md` | Extension used by the `new` command. |
| `pygments` | `true` | Enable code highlighting support. |

All path-like values must stay relative to the site root and must not contain `..`. The source, destination, attachment, and theme directories must not overlap.

## Project Pages URLs

For a repository site hosted at `https://example.github.io/project`, set:

```yaml
url: https://example.github.io
root: /project
```

Keep the repository path in `root`, not in both `url` and `root`. Simiki3 uses the two fields together when generating absolute feed links.
