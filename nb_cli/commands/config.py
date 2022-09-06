from email.policy import default

import click

from nb_cli.utils import ClickAliasedCommand
from nb_cli.handlers import config_no_subcommand


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
@click.option("-e", "--element", multiple=True, default=[])
@click.argument("key", nargs=1, required=False)
@click.argument("value", nargs=1, required=False)
def config(file, list, unset, key, value, element):
    """Modify config file of your project"""
    config_no_subcommand(file, list, unset, key, value, element)
