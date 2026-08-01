---
title: 部署
date: 2026-08-01
category: zh
lang: zh
translation: /simiki3/en/deployment.html
description: 使用 GitHub Pages 或其他静态托管服务发布 Simiki3 站点。
summary: 使用 GitHub Pages 或其他静态托管服务发布 Simiki3 站点。
---

# 部署

Simiki3 生成普通的 HTML、CSS、XML 和复制后的资源，任何静态 Web 托管服务都可以提供 `output/` 目录。

## GitHub Pages

先在本地构建站点：

```bash
uv run simiki3 build docs
```

本仓库的 `.github/workflows/pages.yml` 会在 `main` 分支推送时构建 `docs/`，将 `docs/output/` 上传为 Pages artifact，并使用官方 GitHub Pages actions 部署。也可以从 Actions 页面手动运行工作流。

本站使用以下配置：

```yaml
url: https://hmgle.github.io
root: /simiki3
```

首次部署时，如果 GitHub 没有自动配置 Pages，可能需要在仓库设置中将 Pages source 设置为 **GitHub Actions**。

## 其他静态托管服务

运行 `simiki3 build SITE`，然后上传 `SITE/output/` 的内容。将 `root` 设置为托管服务使用的 URL 前缀，并在主题链接中保持相同前缀。
