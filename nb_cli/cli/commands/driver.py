import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import search_driver, install_driver, driver_no_subcommand


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def driver(ctx: click.Context):
    """Manage Bot Driver."""
    if ctx.invoked_subcommand is None:
        driver_no_subcommand()


@driver.command()
def list():
    """List nonebot builtin drivers."""
    search_driver("")


@driver.command()
@click.argument("name", nargs=1)
def search(name):
    """Search for nonebot builtin driver."""
    search_driver(name)


@driver.command(aliases=["add"])
@click.option("-i", "--index", default=None)
@click.argument("name", nargs=1, required=False)
def install(name, index):
    """Install nonebot driver."""
    install_driver(name, index)
