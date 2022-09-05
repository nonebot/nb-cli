import click

from nb_cli.config import ConfigManager
from nb_cli.handlers import update_config
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
    "--list",
    is_flag=True,
    default=False,
    show_default=True,
    help="List configuration settings",
)
@click.option(
    "--unset",
    is_flag=True,
    default=False,
    show_default=True,
    help="Unset configuration setting",
)
@click.argument("key", nargs=1, required=False)
@click.argument("value", nargs=1, required=False)
def config(file, list, unset, key, value):
    """Modify config file of your project"""
    config = ConfigManager.get_local_config(file)

    if list:
        config.list()
    elif unset:
        update_config(config, key, None)
    else:
        if key is not None and value is not None:
            update_config(config, key, value)
