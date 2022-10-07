import click

from nb_cli.utils import ClickAliasedCommand
from nb_cli.handlers import run_bot, create_project, generate_script


@click.command(cls=ClickAliasedCommand, aliases=["create"])
@click.option(
    "-f",
    "--full",
    is_flag=True,
    default=False,
    show_default=True,
    help="Whether to use full project template or simplified one.",
)
def init(full):
    """Init a NoneBot Project."""
    if full:
        create_project()
    else:
        create_project("bootstrap")


@click.command(cls=ClickAliasedCommand)
@click.option(
    "-c",
    "--config",
    default="pyproject.toml",
    show_default=True,
    help="Config file of your bot",
)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="The file script saved to",
)
def generate(config, file):
    generate_script(config, file)


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
