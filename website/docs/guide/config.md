---
sidebar_position: 6
description: 项目脚本配置

options:
  menu:
    weight: 60
    category: guide
---

# 项目脚本配置

在 Bot 实际维护的过程中，常常会出现需要通过命令行对项目进行管理的情况，NoneBot CLI 设计了命令拓展来解决这一问题。

通过命令拓展，你可以创建一个 `nb <script>` 命令执行脚本。

## 注册脚本

命令拓展使用 Python 的 `entry_points` 机制注册脚本。

例如 setuptools / pdm 等 PEP621 格式:

```toml {2} title="pyproject.toml"
[project.entry-points.nb_scripts]
foo = "awesome_bot.module:function"
```

Poetry 格式:

```toml {15} title="pyproject.toml"
[tool.poetry.plugins.nb_scripts]
foo = "awesome_bot.module:function"
```

## 使用脚本

注册后，命令行即可直接调用:

```shell
nb foo
```

或者使用交互式命令行:

```shell
$ nb
Welcome to NoneBot CLI!
[?] What do you want to do?
  > Run script foo
```
