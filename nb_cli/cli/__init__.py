from pathlib import Path
from typing import List, cast

import click
from noneprompt import Choice, ListPrompt, CancelledError

from nb_cli import __version__
from nb_cli.handlers import draw_logo
from nb_cli.config import ConfigManager
from nb_cli.consts import CONFIG_KEY, MANAGER_KEY

from .customize import CLIMainGroup
from .customize import CLI_DEFAULT_STYLE as CLI_DEFAULT_STYLE
from .customize import ClickAliasedGroup as ClickAliasedGroup
from .customize import ClickAliasedCommand as ClickAliasedCommand


@click.group(cls=CLIMainGroup, invoke_without_command=True)
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s: nonebot cli version %(version)s",
)
@click.option(
    "-c", "--config", default="pyproject.toml", help="Config file path"
)
@click.option("-e", "--encoding", default="utf-8", help="Config file encoding")
@click.option(
    "-py", "--python", default="python", help="Python executable path"
)
@click.pass_context
def cli(ctx: click.Context, config: str, encoding: str, python: str):
    # prepare for cli context
    manager = ConfigManager(Path(config), encoding)
    config_data = manager.get_config()
    config_data.nb_cli.python = python

    ctx.meta[MANAGER_KEY] = manager
    ctx.meta[CONFIG_KEY] = config_data

    # postpone scripts discovery, only when needed (invoked)
    # see {ref}`CLIMainGroup.get_command <nb_cli.cli.customize.CLIMainGroup.get_command>`

    if ctx.invoked_subcommand is None:
        command = cast(CLIMainGroup, ctx.command)

        # auto discover sub commands and scripts
        choices: List[Choice[click.Command]] = []
        for sub_cmd_name in command.list_commands(ctx):
            if sub_cmd := command.get_command(ctx, sub_cmd_name):
                choices.append(
                    Choice(
                        sub_cmd.help or f"Run subcommand {sub_cmd.name}",
                        sub_cmd,
                    )
                )

        draw_logo()
        click.echo("\n\b")
        click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

        # prompt user to choose
        try:
            result = ListPrompt(
                "What do you want to do?", choices=choices
            ).prompt(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit(0)

        sub_cmd = result.data
        ctx.forward(sub_cmd)


from .commands import run, create, generate

cli.add_command(run)
cli.add_command(create)
cli.add_command(generate)
