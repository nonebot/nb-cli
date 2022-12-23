from pathlib import Path

import click

from nb_cli import __version__
from nb_cli.commands.self import self
from nb_cli.utils import CLIMainGroup
from nb_cli.config import ConfigManager
from nb_cli.commands.config import config
from nb_cli.commands.driver import driver
from nb_cli.commands.plugin import plugin
from nb_cli.commands.adapter import adapter
from nb_cli.handlers import handle_no_subcommand
from nb_cli.consts import CONFIG_KEY, MANAGER_KEY
from nb_cli.commands.main import run, init, generate


@click.group(cls=CLIMainGroup, invoke_without_command=True)
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s: nonebot cli version %(version)s",
)
@click.option(
    "-c", "--config", default="pyproject.toml", help="config file path"
)
@click.option("-e", "--encoding", default="utf-8", help="config file encoding")
@click.option(
    "-py", "--python", default="python", help="python executable path"
)
@click.pass_context
def cli(ctx: click.Context, config: str, encoding: str, python: str):
    manager = ConfigManager(Path(config), encoding)
    config_data = manager.get_config()
    config_data.nb_cli.python = python

    ctx.meta[MANAGER_KEY] = manager
    ctx.meta[CONFIG_KEY] = config_data

    if ctx.invoked_subcommand is None:
        handle_no_subcommand(ctx)


cli.add_command(init)
cli.add_command(generate)
cli.add_command(run)

cli.add_command(config)

cli.add_command(adapter)
cli.add_command(plugin)
cli.add_command(driver)
cli.add_command(self)
