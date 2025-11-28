from typing import cast
from pathlib import Path

import click
from noneprompt import Choice, ListPrompt, ConfirmPrompt, CancelledError

from nb_cli import _, __version__
from nb_cli.handlers import draw_logo
from nb_cli.config import ConfigManager

from .utils import run_sync as run_sync
from .utils import run_async as run_async
from .customize import CLIMainGroup as CLIMainGroup
from .utils import CLI_DEFAULT_STYLE as CLI_DEFAULT_STYLE
from .customize import ClickAliasedGroup as ClickAliasedGroup
from .customize import ClickAliasedCommand as ClickAliasedCommand


@click.command  # this command only appears in interactive mode.
@click.pass_context
@run_async
async def exit_(ctx: click.Context):
    if await ConfirmPrompt(_("Are you sure to exit NB CLI?"), True).prompt_async(
        style=CLI_DEFAULT_STYLE
    ):
        ctx.exit()


@click.command  # this command only appears in interactive mode.
def back_():
    # nothing to do, just to keep a command to avoid type violation
    return


def _set_global_working_dir(
    ctx: click.Context, param: click.Option, value: Path | None
):
    ConfigManager._global_working_dir = value


def _set_global_python_path(ctx: click.Context, param: click.Option, value: str | None):
    ConfigManager._global_python_path = value


def _set_global_use_venv(ctx: click.Context, param: click.Option, value: bool):
    ConfigManager._global_use_venv = value


@click.group(
    cls=CLIMainGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    __version__,
    "-V",
    "--version",
    prog_name="nb",
    message="%(prog)s: nonebot cli version %(version)s",
)
@click.option(
    "-d",
    "--cwd",
    default=None,
    help=_("The working directory."),
    type=Path,
    is_eager=True,
    expose_value=False,
    callback=_set_global_working_dir,
)
@click.option(
    "-py",
    "--python",
    default=None,
    help=_("Python executable path."),
    is_eager=True,
    expose_value=False,
    callback=_set_global_python_path,
)
@click.option(
    "--venv/--no-venv",
    default=True,
    help=_("Auto detect virtual environment."),
    is_eager=True,
    expose_value=False,
    callback=_set_global_use_venv,
)
@click.pass_context
@run_async
async def cli(ctx: click.Context):
    # Postpone scripts discovery, only when needed (invoked). See
    # {ref}`CLIMainGroup.get_command <nb_cli.cli.customize.CLIMainGroup.get_command>`

    if ctx.invoked_subcommand is not None:
        return

    command = cast(CLIMainGroup, ctx.command)

    # auto discover sub commands and scripts
    choices: list[Choice[click.Command]] = []
    for sub_cmd_name in await run_sync(command.list_commands)(ctx):
        if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help
                    or _("Run subcommand {sub_cmd.name!r}").format(sub_cmd=sub_cmd),
                    sub_cmd,
                )
            )
    _exit_choice = Choice(_("Exit NB CLI."), exit_)
    choices.append(_exit_choice)

    click.secho(draw_logo(), fg="cyan", bold=True)
    click.echo("\n\b")
    click.secho(_("Welcome to NoneBot CLI!"), fg="green", bold=True)

    while True:
        # prompt user to choose
        try:
            result = await ListPrompt(
                _("What do you want to do?"), choices=choices
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            result = _exit_choice

        sub_cmd = result.data
        ctx.params["can_back_to_parent"] = True
        await run_sync(ctx.invoke)(sub_cmd)


from .commands import (
    run,
    self,
    create,
    driver,
    plugin,
    adapter,
    generate,
    upgrade_format,
    downgrade_format,
)

cli.add_command(create)
cli.add_command(run)
cli.add_command(generate)
cli.add_command(upgrade_format)
cli.add_command(downgrade_format)

cli.add_command(plugin)

cli.add_command(adapter)

cli.add_command(driver)

cli.add_command(self)
