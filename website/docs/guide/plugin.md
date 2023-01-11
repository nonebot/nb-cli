---
sidebar_position: 7
description: CLI 插件配置

options:
  menu:
    weight: 70
    category: guide
---

# CLI 插件配置

CLI 插件运行在 nb-cli 所在环境中，可以调用 nb-cli 所提供的功能或者扩展其功能，来实现更丰富便捷的开发体验。

## 注册插件

插件使用 Python 的 `entry_points` 机制注册。

例如 setuptools / pdm 等 PEP621 格式:

```toml title="pyproject.toml"
[project.entry-points.nb]
plugin_name = "cli_plugin.plugin:install"
```

Poetry 格式:

```toml title="pyproject.toml"
[tool.poetry.plugins.nb_scripts]
plugin_name = "cli_plugin.plugin:install"
```

## 编写插件

如扩展 CLI 命令：

1. 使用 click 编写 CLI 命令

   ```python title="cli_plugin/cli.py"
   from typing import List, cast

   import click
   from noneprompt import Choice, ListPrompt, CancelledError
   from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async


   @click.group(cls=ClickAliasedGroup, invoke_without_command=True)
   @click.pass_context
   @run_async
   async def command_name(ctx: click.Context):
       """Command help."""
       if ctx.invoked_subcommand is not None:
           return

       command = cast(ClickAliasedGroup, ctx.command)

       # auto discover sub commands and scripts
       choices: List[Choice[click.Command]] = []
       for sub_cmd_name in await run_sync(command.list_commands)(ctx):
           if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
               choices.append(
                   Choice(
                       sub_cmd.help or f"Run subcommand {sub_cmd.name}",
                       sub_cmd,
                   )
               )

       try:
           result = await ListPrompt(
               "What do you want to do?", choices=choices
           ).prompt_async(style=CLI_DEFAULT_STYLE)
       except CancelledError:
           ctx.exit()

       sub_cmd = result.data
       await run_sync(ctx.invoke)(sub_cmd)
   ```

2. 编写 `install` 函数

   ```python title="cli_plugin/plugin.py"
   from typing import cast

   from nb_cli.cli import CLIMainGroup, cli

   from .cli import command_name


   def install():
       cli_ = cast(CLIMainGroup, cli)
       cli_.add_command(command_name)
       # cli_.add_aliases("command_name", ["command_alias"])
   ```

3. 在 `pyproject.toml` 中注册插件后，测试效果

   ```shell
   nb command_name --help
   ```
