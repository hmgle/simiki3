---
title: CLI 参考
date: 2026-08-01
category: zh/reference
lang: zh
translation: /simiki3/en/reference/cli.html
description: Simiki3 命令行界面的完整参考。
summary: Simiki3 命令行界面的完整参考。
---

# CLI 参考

运行 `simiki3 --help` 可以查看命令帮助。主要命令如下：

| 命令 | 用途 |
| --- | --- |
| `simiki3 init [PATH]` | 创建包含配置、内容、输出目录和主题的站点骨架。 |
| `simiki3 new TITLE --path PATH` | 创建带 front matter 的 Markdown 页面。 |
| `simiki3 build [PATH]` | 将已发布的 Markdown 页面渲染为静态 HTML。 |
| `simiki3 serve [PATH] --watch` | 构建并本地提供输出目录，文件变化时自动重新构建。 |
| `simiki3 update [PATH]` | 更新内置配置模板和主题资源。 |
| `simiki3 theme list` | 列出 Simiki3 内置主题。 |
| `simiki3 theme sync THEME --path PATH` | 将内置主题复制到已有站点。 |
| `simiki3 validate LEGACY NEW` | 比较两个构建目录中的指定文件。 |
| `simiki3 migrate audit PATH` | 检查旧版站点并报告迁移阻塞问题。 |
| `simiki3 migrate fix PATH` | 应用安全的迁移修复，也可以先执行 dry run。 |
| `simiki3 goals` | 显示当前项目路线图。 |

## 构建选项

使用 `--include-drafts` 可以包含 front matter 中设置 `draft: true` 的页面：

```bash
simiki3 build my-wiki --include-drafts
```

当希望由 build 命令监控源文件时，可以使用 `build` 的 `--watch`。通常使用 `serve --watch` 进行浏览器预览更方便。

## 迁移选项

始终先审计旧站点：

```bash
simiki3 migrate audit legacy-site
simiki3 migrate fix legacy-site --dry-run
simiki3 migrate fix legacy-site
```

迁移修复默认会创建备份，请在删除旧文件前检查备份内容。
