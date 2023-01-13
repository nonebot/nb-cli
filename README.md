<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://cli.nonebot.dev/"><img src="https://cli.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# NB CLI

_✨ NoneBot2 命令行工具 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/nonebot/nb-cli/master/LICENSE">
    <img src="https://img.shields.io/github/license/nonebot/nb-cli" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nb-cli">
    <img src="https://img.shields.io/pypi/v/nb-cli" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8+-blue" alt="python">
  <a href="https://github.com/nonebot/nb-cli/actions/workflows/website-deploy.yml">
    <img src="https://github.com/nonebot/nb-cli/actions/workflows/website-deploy.yml/badge.svg?branch=master&event=push" alt="site"/>
  </a>
  <a href="https://results.pre-commit.ci/latest/github/nonebot/nb-cli/master">
    <img src="https://results.pre-commit.ci/badge/github/nonebot/nb-cli/master.svg" alt="pre-commit" />
  </a>
  <br />
  <a href="https://jq.qq.com/?_wv=1027&k=5OFifDh">
    <img src="https://img.shields.io/badge/QQ%E7%BE%A4-768887710-orange?style=flat-square" alt="QQ Chat Group">
  </a>
  <a href="https://qun.qq.com/qqweb/qunpro/share?_wv=3&_wwv=128&appChannel=share&inviteCode=7b4a3&appChannel=share&businessType=9&from=246610&biz=ka">
    <img src="https://img.shields.io/badge/QQ%E9%A2%91%E9%81%93-NoneBot-5492ff?style=flat-square" alt="QQ Channel">
  </a>
  <a href="https://t.me/botuniverse">
    <img src="https://img.shields.io/badge/telegram-botuniverse-blue?style=flat-square" alt="Telegram Channel">
  </a>
  <a href="https://discord.gg/VKtE6Gdc4h">
    <img src="https://discordapp.com/api/guilds/847819937858584596/widget.png?style=shield" alt="Discord Server">
  </a>
</p>

<p align="center">
  <a href="https://cli.nonebot.dev/">文档</a>
  ·
  <a href="https://cli.nonebot.dev/docs/guide/installation">安装</a>
  ·
  <a href="https://v2.nonebot.dev/">NoneBot 文档</a>
</p>

## 功能

- 创建新的 Nonebot 项目
- 启动 Nonebot
- 管理插件
  - 创建新的插件
  - 搜索/安装/更新/卸载在官方商店上发布的插件
- 管理适配器
  - 创建新的适配器
  - 搜索/安装/更新/卸载在官方商店上发布的适配器
- 管理驱动器
  - 搜索/安装/更新/卸载在官方商店上发布的驱动器
- 支持 CLI 插件和运行脚本

## 使用

完整使用文档请参考 [文档](https://cli.nonebot.dev/)。

### 安装

使用 pipx 安装

```shell
pipx install nb-cli
```

### 命令行使用

```shell
nb --help
```

> **Warning**
>
> 如果找不到 `nb` 命令，请尝试 `pipx ensurepath` 来添加路径到环境变量

- `nb create (init)` 创建新的 NoneBot 项目
- `nb run` 在当前目录启动 NoneBot
- `nb generate` 在当前目录生成启动脚本
- `nb driver` 管理驱动器
- `nb plugin` 管理插件
- `nb adapter` 管理适配器
- `nb self` 管理 CLI 内部环境
- `nb <script>` 运行脚本

### 交互式使用

```shell
nb
```

## 开发

### 翻译

生成模板

```shell
pdm run extract
```

初始化语言翻译文件或者更新现有语言翻译文件

```shell
pdm run init en_US
```

更新语言翻译文件

```shell
pdm run update
```

编译语言翻译文件

```shell
pdm run compile
```
