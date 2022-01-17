import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import (
    create_adapter,
    search_adapter,
    update_adapter,
    install_adapter,
    adapter_no_subcommand,
)


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def adapter(ctx: click.Context):
    """Manage Bot Adapter."""   
    if ctx.invoked_subcommand is None:
        adapter_no_subcommand()


@adapter.command()
def list():
    """List nonebot adapters published on nonebot homepage."""
    search_adapter("")


@adapter.command()
@click.argument("name", nargs=1, required=False)
def search(name):
    """Search for nonebot adapter published on nonebot homepage."""
    search_adapter(name)


@adapter.command(aliases=["add"])
@click.option("-i", "--index", default=None)
@click.argument("name", nargs=1)
def install(name, index):
    """Install nonebot adapter."""
    install_adapter(name, index)


@adapter.command()
@click.option("-i", "--index", default=None)
@click.argument("name", nargs=1)
def update(name, index):
    """Update nonebot adapter."""
    update_adapter(name, index)


@adapter.command(aliases=["create"])
@click.argument("name", required=False)
@click.option(
    "-d",
    "--adapter-dir",
    type=click.Path(exists=True, file_okay=False, writable=True),
)
def new(name, adapter_dir):
    """Create a custom nonebot adapter."""
    create_adapter(name, adapter_dir)
