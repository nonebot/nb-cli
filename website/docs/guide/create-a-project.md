---
sidebar_position: 2
description: 创建项目
---

# 创建项目

运行以下命令来创建一个新项目：

```shell
nb create
```

跟随指引填入参数后，CLI 将在当前目录下，使用之前所填入的项目名，创建一个文件夹用于存放 NoneBot 项目。

:::warning 注意
新版本 CLI 在默认情况下会创建一个最简的 NoneBot 项目，以便用户进行部署。

对于开发者，应该使用 `nb create --full`。
:::

CLI 所创建的项目目录结构可参考 [NoneBot 文档](https://v2.nonebot.dev/docs/tutorial/create-project#%E7%9B%AE%E5%BD%95%E7%BB%93%E6%9E%84)

```shell
nb create --help
Usage: nb create [OPTIONS]

  Init a NoneBot Project.

Options:
  -f, --full  Whether to use full project template or simplified one
  --help      Show this message and exit.
```
