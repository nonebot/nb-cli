import sys
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async
from nb_cli.handlers import call_pip_update, call_pip_install, call_pip_uninstall


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
@run_async
async def self(ctx: click.Context):
    """Manage NB CLI."""

    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

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


@self.command(aliases=["add"])
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    """Install dependency to cli venv."""
    if name is None:
        try:
            name = await InputPrompt("Package name you want to install?").prompt_async(
                style=CLI_DEFAULT_STYLE
            )
        except CancelledError:
            ctx.exit()

    proc = await call_pip_install(name, pip_args, sys.executable)
    await proc.wait()


@self.command()
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(pip_args: Optional[List[str]]):
    """Update nonebot plugin."""
    proc = await call_pip_update("nb-cli", pip_args, sys.executable)
    await proc.wait()


@self.command(aliases=["remove"])
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    """Uninstall nonebot cli dependency from cli venv."""
    if name is None:
        try:
            name = await InputPrompt(
                "Package name you want to uninstall?"
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    proc = await call_pip_install(name, pip_args, sys.executable)
    await proc.wait()
