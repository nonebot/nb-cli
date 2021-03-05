import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import search_adapter, create_adapter


@click.group(cls=ClickAliasedGroup)
def adapter():
    """Manage Bot Adapter."""
    pass


@adapter.command()
def list():
    """List nonebot adapters published on nonebot homepage."""
    search_adapter("")


@adapter.command()
@click.argument("name", nargs=1)
def search(name):
    """Search for nonebot adapter published on nonebot homepage."""
    search_adapter(name)


@adapter.command(aliases=["create"])
@click.argument("name", required=False)
@click.option("-d",
              "--adapter-dir",
              type=click.Path(exists=True, file_okay=False, writable=True))
def new(name, adapter_dir):
    """Create a custom nonebot adapter."""
    create_adapter(name, adapter_dir)
