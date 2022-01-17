import click

from nb_cli.utils import ClickAliasedCommand
from nb_cli.handlers import run_bot, create_project


@click.command(cls=ClickAliasedCommand, aliases=["create"])
def init():
    """Create A NoneBot Project."""
    create_project()


@click.command(cls=ClickAliasedCommand, aliases=["start"])
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="Entry file of your bot",
)
@click.option(
    "-a",
    "--app",
    default="app",
    show_default=True,
    help="ASGI application of your bot",
)
def run(file, app):
    """Run the Bot in Current Folder."""
    run_bot(file, app)
