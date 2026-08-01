---
title: 迁移
date: 2026-08-01
category: zh/guides
lang: zh
translation: /simiki3/en/guides/migration.html
description: 审计旧版 Simiki 站点并迁移到 Simiki3。
summary: 审计旧版 Simiki 站点并迁移到 Simiki3。
---

# 迁移

Simiki3 为常见的旧版 Simiki 布局提供迁移辅助工具。迁移流程强调可检查性：先审计，再预览修复，最后带备份执行。

## 审计站点

```bash
simiki3 migrate audit legacy-site
```

审计会检查配置规范化、旧版 `layout: post`、缺失的页面日期、页面解析错误以及缺失的内置主题资源。

## 预览并应用修复

```bash
simiki3 migrate fix legacy-site --dry-run
simiki3 migrate fix legacy-site
```

默认情况下，修复会规范化配置、更新页面 front matter、在可用时同步内置主题，并在修改文件前创建 `.bak` 备份。

## 检查结果

构建迁移后的站点；如果同时保留旧构建目录，可以比较两个构建结果：

```bash
simiki3 build legacy-site
simiki3 validate old-output legacy-site/output
```

迁移工具不会自动改写任意链接，也不会移植自定义旧主题，这些部分需要手动检查。
