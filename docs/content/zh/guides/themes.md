---
title: 主题
date: 2026-08-01
category: zh/guides
lang: zh
translation: /simiki3/en/guides/themes.html
description: 选择、同步并自定义 Simiki3 主题。
summary: 选择、同步并自定义 Simiki3 主题。
---

# 主题

Simiki3 使用 `_config.yml` 中配置的主题渲染页面。新建站点时，配置的内置主题会复制到 `themes/` 下。

## 列出并同步内置主题

```bash
simiki3 theme list
simiki3 theme sync default --path my-wiki
```

只有在明确要覆盖本地主题文件时，才使用 `theme sync` 的 `--force`。

## 主题结构

主题包含 Jinja 模板和可选的静态资源：

```text
themes/my-theme/
├── static/
│   └── css/
└── templates/
    ├── base.html
    ├── index.html
    └── page.html
```

`page.html` 是必需模板。`index.html` 控制生成的目录首页，`base.html` 可以为继承它的主题提供共享 HTML 结构。

## 模板上下文

模板会收到 `site`、`page`、`pages` 和 `default_home_page`。站点元数据位于 `site`，渲染后的 Markdown HTML 位于 `page.content`。对于已经渲染的 HTML，应使用 `safe` filter。

构建过程会把 `static/` 下的文件复制到生成站点的 `static/` 目录。如果站点部署在域名根路径下方，应使用 `site.root_url` 为链接添加正确的 URL 前缀。
