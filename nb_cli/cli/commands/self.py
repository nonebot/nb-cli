import sys
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli import _
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async
from nb_cli.handlers import (
    call_pip_list,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage NB CLI.")
)
@click.pass_context
@run_async
async def self(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: List[Choice[click.Command]] = []
    for sub_cmd_name in await run_sync(command.list_commands)(ctx):
        if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help
                    or _("Run subcommand {sub_cmd.name!r}").format(sub_cmd=sub_cmd),
                    sub_cmd,
                )
            )

    try:
        result = await ListPrompt(
            _("What do you want to do?"), choices=choices
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    sub_cmd = result.data
    await run_sync(ctx.invoke)(sub_cmd)


@self.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install package to cli venv."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    if name is None:
        try:
            name = await InputPrompt(
                _("Package name you want to install?")
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    proc = await call_pip_install(name, pip_args, python_path=sys.executable)
    await proc.wait()


@self.command(
    context_settings={"ignore_unknown_options": True}, help=_("Update cli self.")
)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(pip_args: Optional[List[str]]):
    proc = await call_pip_update("nb-cli", pip_args, python_path=sys.executable)
    await proc.wait()


@self.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall package from cli venv."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    if name is None:
        try:
            name = await InputPrompt(
                _("Package name you want to uninstall?")
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    proc = await call_pip_uninstall(name, pip_args, python_path=sys.executable)
    await proc.wait()


@self.command(
    context_settings={"ignore_unknown_options": True},
    help=_("List installed packages in cli venv."),
)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def list(pip_args: Optional[List[str]]):
    proc = await call_pip_list(pip_args, python_path=sys.executable)
    await proc.wait()
