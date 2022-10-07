---
sidebar_position: 3
description: 启动 Bot
---

# 启动 Bot

运行以下命令在**当前执行目录**下启动 Bot：

```shell
nb run
```

:::warning 注意
新版本 CLI 在最简项目环境下会使用 pyproject.toml 内的配置项自行生成启动脚本并运行。

对于目录下已有 `bot.py` 的项目，CLI 会使用该脚本运行 bot。
:::

```shell
nb run --help
Usage: nb run [OPTIONS]

  Run the Bot in Current Folder.

Options:
  -f, --file TEXT    Entry file of your bot  [default: bot.py]
  -c, --config TEXT  Config file of your bot  [default: pyproject.toml]
  --help             Show this message and exit.
```

# 生成启动脚本

运行以下命令在当前执行目录下生成启动脚本，一般用于 docker 部署。

```shell
nb generate --help
Usage: nb generate [OPTIONS]

Options:
  -c, --config TEXT  Config file of your bot  [default: pyproject.toml]
  -f, --file TEXT    The file script saved to  [default: bot.py]
  --help             Show this message and exit.
```
