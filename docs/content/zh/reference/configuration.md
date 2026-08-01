---
title: 配置
date: 2026-08-01
category: zh/reference
lang: zh
translation: /simiki3/en/reference/configuration.html
description: 配置站点元数据、路径、URL 前缀和主题。
summary: 配置站点元数据、路径、URL 前缀和主题。
---

# 配置

Simiki3 从站点根目录的 `_config.yml` 读取配置。最小配置示例：

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

## 主要字段

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `url` | 空 | 用于生成绝对 Atom feed 链接的公开站点 URL。 |
| `title` | `Simiki Wiki` | 主题显示的站点标题。 |
| `keywords` | 空 | 逗号分隔的元数据关键词。 |
| `description` | 空 | 用于元数据和主题的站点描述。 |
| `author` | 空 | 页脚显示的作者。 |
| `root` | `/` | 项目站点的 URL 前缀，例如 `/simiki3`。 |
| `source` | `content` | 相对于站点根目录的 Markdown 源目录。 |
| `destination` | `output` | 相对于站点根目录的生成目录。 |
| `attach` | `attach` | 会被复制到输出目录的附件目录。 |
| `themes_dir` | `themes` | 已安装主题目录。 |
| `theme` | `simple2` | 选中的渲染主题。 |
| `default_ext` | `md` | `new` 命令使用的文件扩展名。 |
| `pygments` | `true` | 是否启用代码高亮支持。 |

所有路径字段都必须相对于站点根目录，不能包含 `..`。源目录、输出目录、附件目录和主题目录之间不能互相重叠。

## Project Pages URL

如果仓库站点托管在 `https://example.github.io/project`，配置为：

```yaml
url: https://example.github.io
root: /project
```

将仓库路径放在 `root` 中，不要同时放入 `url` 和 `root`。Simiki3 会组合两个字段生成绝对 feed 链接。
