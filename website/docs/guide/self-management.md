---
sidebar_position: 6
description: CLI 自身管理
---

# CLI 自身管理

CLI 处于独立的虚拟环境中运行，由外界直接管理 CLI 的环境在不使用 pipx 的情况下较为困难。

因此，CLI 向外提供了以下的命令，便于外界对 CLI 自身的环境进行操作。

- `nb self` 管理 CLI 内部环境
  - `nb self list` 列出 CLI 环境中所有包
  - `nb self install (add)` 在 CLI 环境安装包
  - `nb self update` 更新 CLI 环境包
  - `nb self uninstall (remove)` 卸载 CLI 环境包

:::warning 注意
在一般情况下，CLI 的内部环境不需要额外的手动干预。

在对 CLI 的内部环境进行操作前，请清楚该命令会对内部环境带来的影响。
:::
