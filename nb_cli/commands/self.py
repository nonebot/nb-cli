import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers.self import (
    self_update,
    self_install,
    self_uninstall,
    self_no_subcommand,
)


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def self(ctx: click.Context):
    """Manage Bot Plugin."""
    if ctx.invoked_subcommand is None:
        self_no_subcommand()


@self.command(aliases=["add"])
@click.option("-i", "--index", default=None)
@click.argument("name", nargs=1, required=False)
def install(name, index):
    """Install dependency to cli venv."""
    self_install(name, index)


@self.command()
@click.option("-i", "--index", default=None)
def update(index):
    """Update nonebot plugin."""
    self_update(index)


@self.command(aliases=["remove"])
@click.argument("name", nargs=1)
def uninstall(name):
    """Uninstall nonebot cli dependency from cli venv."""
    self_uninstall(name)
