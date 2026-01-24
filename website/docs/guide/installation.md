---
sidebar_position: 1
description: 安装 NoneBot CLI

options:
  menu:
    - category: guide
      weight: 10
---

# 安装

## 环境要求

NoneBot CLI 仅支持 Python 3.10 以上版本。

## 通过 pipx 安装

pipx 是专为 Python CLI 应用设计的工具，实现了 CLI 应用的环境隔离。同时，pipx 也会接管 NoneBot CLI 及其依赖的升级与卸载。

请参考 [pipx 文档](https://pypa.github.io/pipx/installation/) 来安装 pipx。

```shell title="安装 NoneBot CLI"
pipx install nb-cli
```

```shell title="升级 NoneBot CLI"
pipx upgrade nb-cli
```

```shell title="卸载 NoneBot CLI"
pipx uninstall nb-cli
```

## 通过 uv tool 安装

uv (by Astral) 是一个飞快的 Python 包与项目管理器，使用 Rust 语言编写。其也拥有工具集成管理的功能。

请参考 [uv 文档](https://docs.astral.sh/uv/getting-started/installation/) 来安装 uv。

```shell title="直接运行最新 NoneBot CLI"
uvx --from nb-cli@latest nb
```

```shell title="安装 NoneBot CLI"
uv tool install nb-cli@latest
```

```shell title="运行已安装的 NoneBot CLI"
uvx --from nb-cli nb
# 或
uv tool run --from nb-cli nb
```

```shell title="升级 NoneBot CLI"
uv tool upgrade nb-cli
```

```shell title="卸载 NoneBot CLI"
uv tool uninstall nb-cli
```
