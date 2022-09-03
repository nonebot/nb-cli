import click

from nb_cli.config import ConfigManager
from nb_cli.utils import ClickAliasedCommand


@click.command(cls=ClickAliasedCommand)
@click.option(
    "-f",
    "--file",
    default="pyproject.toml",
    show_default=True,
    help="Config file of your bot",
)
@click.option(
    "-g",
    "--global",
    "is_global",
    is_flag=True,
    default=False,
    show_default=True,
    help="Modify cli global config or bot local config",
)
@click.option(
    "-l",
    "--local",
    "is_local",
    is_flag=True,
    default=True,
    show_default=True,
    help="Modify cli global config or bot local config",
)
def config(file, is_global, is_local):
    """Modify config file of your bot"""
    if is_global:
        config = ConfigManager.get_local_config(file)
    elif is_local:
        config = ConfigManager.get_global_config()
