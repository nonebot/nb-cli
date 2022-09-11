---
sidebar_position: 7
description: CLI 配置
---

# CLI 配置

在默认情况下，CLI 会从 `pyproject.toml` 文件中读取或向其写入配置。当然，在 CLI 用到配置文件时，你也可以自行通过各命令的参数指定配置文件的名称。

目前 CLI 支持的配置项：

- reload (bool) 是否启用 cli 内置的 reloader
- plugins (array) 启用的插件列表
- plugin_dirs (array) 启用的插件目录列表
- adapters (array) 启动的适配器列表
- builtin_plugins (array) 启用的内置插件列表
- reload_dirs (array) 需要 reloader 监控的目录
- reload_dirs_excludes (array) 不需要 reloader 监控的目录
- reload_excludes (array) 不需要 reloader 监控的文件
- reload_includes (array) 需要 reloader 监控的文件
