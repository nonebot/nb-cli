import click

from nb_cli.utils import ClickAliasedCommand
from nb_cli.handlers import run_bot, create_project


@click.command(cls=ClickAliasedCommand, aliases=["create"])
def init():
    """Create A NoneBot Project."""
    create_project()


@click.command(cls=ClickAliasedCommand, aliases=["bootstrap"])
def bootstrap():
    """Bootstrap a NoneBot Project."""
    create_project("bootstrap")


@click.command(cls=ClickAliasedCommand, aliases=["start"])
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="Entry file of your bot",
)
@click.option(
    "-c",
    "--config",
    default="pyproject.toml",
    show_default=True,
    help="Config file of your bot",
)
def run(file, config):
    """Run the Bot in Current Folder."""
    run_bot(file, config)
