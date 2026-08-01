---
title: 开发
date: 2026-08-01
category: zh
lang: zh
translation: /simiki3/en/development.html
description: 运行 Simiki3 开发流程和测试套件。
summary: 运行 Simiki3 开发流程和测试套件。
---

# 开发

Simiki3 支持 Python 3.10 及更高版本。仓库使用 `uv` 管理依赖，使用 `pytest` 和 `ruff` 做验证。

## 准备环境

```bash
git clone https://github.com/hmgle/simiki3.git
cd simiki3
uv sync --extra dev
```

## 验证改动

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
uv run --extra dev python -m compileall -q src tests
```

端到端冒烟路径是 `init → build → serve`。主题和迁移行为发生变化时，应增加集成测试覆盖。

## 在本地构建本站文档

这个仓库的文档本身就是一个 Simiki3 站点：

```bash
uv run simiki3 build docs
uv run simiki3 serve docs --watch
```

生成文件写入 `docs/output/`，并且会被 Git 忽略。
