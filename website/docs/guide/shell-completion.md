---
sidebar_position: 9
description: Shell 自动补全

options:
  menu:
    weight: 90
    category: guide
---

# Shell 自动补全

参考[click 文档](https://click.palletsprojects.com/en/8.1.x/shell-completion/)，可以为 click 命令行工具生成 shell 自动补全脚本。

## Bash

保存补全文件

```shell
_NB_COMPLETE=bash_source nb > ~/.nb-complete.bash
```

添加补全到 `~/.bashrc` 文件中

```bash title="~/.bashrc"
. ~/.foo-bar-complete.bash
```

## Zsh

保存补全文件

```shell
_NB_COMPLETE=zsh_source nb > ~/.nb-complete.zsh
```

添加补全到 `~/.zshrc` 文件中

```bash title="~/.zshrc"
. ~/.foo-bar-complete.zsh
```

## Fish

保存补全文件

```shell
_NB_COMPLETE=fish_source nb > ~/.config/fish/completions/nb.fish
```
