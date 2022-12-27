from pathlib import Path
from typing import List, cast

import click
from noneprompt import Choice, ListPrompt, CancelledError

from nb_cli import __version__
from nb_cli.handlers import draw_logo
from nb_cli.config import ConfigManager
from nb_cli.consts import CONFIG_KEY, MANAGER_KEY

from .customize import CLIMainGroup
from .utils import run_sync as run_sync
from .utils import run_async as run_async
from .utils import CLI_DEFAULT_STYLE as CLI_DEFAULT_STYLE
from .customize import ClickAliasedGroup as ClickAliasedGroup
from .customize import ClickAliasedCommand as ClickAliasedCommand


def prepare_config(ctx: click.Context, param: click.Parameter, value: str):
    # prepare for cli context
    manager = ConfigManager(Path(ctx.params["config"]), ctx.params["encoding"])
    config_data = manager.get_config()
    config_data.python = value

    ctx.meta[MANAGER_KEY] = manager
    ctx.meta[CONFIG_KEY] = config_data


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
    "-c",
    "--config",
    default="pyproject.toml",
    help="Config file path.",
    is_eager=True,
)
@click.option(
    "-e",
    "--encoding",
    default="utf-8",
    help="Config file encoding.",
    is_eager=True,
)
@click.option(
    "-py",
    "--python",
    default="python",
    help="Python executable path.",
    is_eager=True,
    callback=prepare_config,
)
@click.pass_context
@run_async
async def cli(ctx: click.Context, config: str, encoding: str, python: str):
    # postpone scripts discovery, only when needed (invoked)
    # see {ref}`CLIMainGroup.get_command <nb_cli.cli.customize.CLIMainGroup.get_command>`

    if ctx.invoked_subcommand is not None:
        return

    command = cast(CLIMainGroup, ctx.command)

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

    click.secho(draw_logo(), fg="cyan", bold=True)
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    # prompt user to choose
    try:
        result = await ListPrompt(
            "What do you want to do?", choices=choices
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit(0)

    sub_cmd = result.data
    await run_sync(ctx.invoke)(sub_cmd)


from .commands import run, self, create, plugin, adapter, generate

cli.add_command(create)
cli.add_command(run)
cli.add_command(generate)

cli.add_command(plugin)

cli.add_command(adapter)

cli.add_command(self)
