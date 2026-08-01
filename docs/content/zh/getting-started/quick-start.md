---
title: 快速开始
date: 2026-08-01
category: zh/getting-started
lang: zh
translation: /simiki3/en/getting-started/quick-start.html
description: 用几个命令创建、构建并预览 Simiki3 站点。
summary: 用几个命令创建、构建并预览 Simiki3 站点。
---

# 快速开始

创建站点、添加页面、构建并启动本地预览服务器：

```bash
simiki3 init my-wiki
simiki3 new "First page" --path my-wiki --category intro
simiki3 build my-wiki
simiki3 serve my-wiki --watch
```

生成的站点结构如下：

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

将 Markdown 源文件放在 `content/` 下。Simiki3 会把生成的 HTML、CSS、feed 和附件写入 `output/`。

## 手动创建页面

每个页面都可以使用 YAML front matter 开头：

```markdown
---
title: 项目笔记
date: 2026-08-01
category: notes
---

# 项目笔记

Markdown 内容写在这里。
```

默认文件扩展名为 `.md`。需要修改源目录或输出目录时，请参考[配置参考](/simiki3/zh/reference/configuration.html)。
