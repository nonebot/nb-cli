---
sidebar_position: 3
description: 启动 Bot

options:
  menu:
    weight: 30
    category: guide
---

# 启动 Bot

:::warning 注意
请在运行命令前，确保已经在项目目录下。如果使用了虚拟环境，确保已经激活。
:::

运行以下命令在**当前执行目录**下启动 Bot：

```shell
nb run
```

:::warning 注意
新版本 CLI 在最简项目环境下会使用 pyproject.toml 内的配置项自行生成启动脚本并运行。

对于目录下已有 `bot.py` 的项目，CLI 会使用该脚本运行 bot。
:::

```shell
$ nb run --help
Usage: nb run [OPTIONS]

  Run the bot in current folder.

Options:
  -d, --cwd TEXT          The working directory.
  -f, --file TEXT         Exist entry file of your bot.  [default: bot.py]
  -r, --reload            Reload the bot when file changed.
  --reload-includes TEXT  Files to watch for changes.
  --reload-excludes TEXT  Files to ignore for changes.
  -h, --help              Show this message and exit.
```

## 生成启动脚本

运行以下命令在当前执行目录下生成启动脚本，一般用于 docker 部署。

```shell
$ nb generate --help
Usage: nb generate [OPTIONS]

  Generate entry file of your bot.

Options:
  -f, --file TEXT  The file script saved to.  [default: bot.py]
  -h, --help       Show this message and exit.
```
