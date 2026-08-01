---
title: 安装
date: 2026-08-01
category: zh/getting-started
lang: zh
translation: /simiki3/en/getting-started/installation.html
description: 安装 Simiki3 并准备本地开发环境。
summary: 安装 Simiki3 并准备本地开发环境。
---

# 安装

Simiki3 需要 Python 3.10 或更高版本。

## 从源码仓库安装

项目使用 [uv](https://docs.astral.sh/uv/) 管理可复现的开发环境：

```bash
git clone https://github.com/hmgle/simiki3.git
cd simiki3
uv sync --extra dev
uv run simiki3 --version
```

`dev` extra 会安装项目使用的测试和 lint 工具。

## 作为已安装命令使用

如果使用已发布的包，请使用你偏好的 Python 包管理器安装 `simiki3`，并确认生成的 `simiki3` 命令位于 `PATH` 中。使用以下命令验证：

```bash
simiki3 --version
```

## 下一步

继续阅读[快速开始](/simiki3/zh/getting-started/quick-start.html)，初始化站点并渲染第一个页面。
