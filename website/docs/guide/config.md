---
sidebar_position: 7
description: 项目基础配置
---

# 项目基础配置

运行以下命令来修改项目配置：

```shell
nb config [KEY] [VALUE]
```

```shell title="例：将 reload 修改为 true"
nb config reload true
```

```shell title="例：将 reload_dirs 修改为 ["src/","folder/"]"
nb config reload_dirs -e src/ -e folder/
```

在默认情况下，CLI 会从项目目录下的 `pyproject.toml` 文件中读取或向其写入配置。

可由 `nb config` 直接进行修改的配置项：

- reload (bool) 是否启用 CLI 内置的 reloader
- plugins (array) NoneBot 插件列表
- plugin_dirs (array) NoneBot 插件目录列表
- adapters (array) NoneBot 适配器列表
- builtin_plugins (array) NoneBot 内置插件列表
- reload_dirs (array) 需要 reloader 监控的目录
- reload_dirs_excludes (array) 不需要 reloader 监控的目录
- reload_excludes (array) 不需要 reloader 监控的文件
- reload_includes (array) 需要 reloader 监控的文件
- cli_plugins CLI 插件列表
- cli_plugin_dirs CLI 插件目录列表

```shell
Usage: nb config [OPTIONS] [KEY] [VALUE]

  Modify config file of your project

Options:
  -f, --file TEXT     Config file of your bot  [default: pyproject.toml]
  --list              List configuration settings
  --unset             Unset configuration setting
  -e, --element TEXT
  --help              Show this message and exit.
```

# 项目命令拓展配置

在 Bot 实际维护的过程中，常常会出现需要输入较长命令的情况，NoneBot CLI 设计了命令拓展来解决这一问题。

通过命令拓展，你可以为较长命令创建一个 `nb <command>` 的别名。

```toml {15} title="例：配置 nb upgrade 作为 python awesome_bot.maintainance:main 的别名"
[tool.nonebot]
plugins = []
plugin_dirs = ["src/plugins"]
adapters = ["nonebot.adapters.onebot.v11"]
builtin_plugins = []
reload_dirs_excludes = []
reload_dirs = ["src"]
reload_includes = []
reload_excludes = []
reload = false
cli_plugins = []
cli_plugin_dirs = []

[tool.nonebot.scripts]
upgrade = "python awesome_bot.maintainance:main"
```
