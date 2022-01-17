import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import (
    create_plugin,
    search_plugin,
    update_plugin,
    install_plugin,
    uninstall_plugin,
    plugin_no_subcommand,
)


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def plugin(ctx: click.Context):
    """Manage Bot Plugin."""
    if ctx.invoked_subcommand is None:
        plugin_no_subcommand()


@plugin.command()
def list():
    """List nonebot plugins published on nonebot homepage."""
    search_plugin("")


@plugin.command()
@click.argument("name", nargs=1)
def search(name):
    """Search for nonebot plugin published on nonebot homepage."""
    search_plugin(name)


@plugin.command(aliases=["add"])
@click.option("-i", "--index", default=None)
@click.option(
    "-f",
    "--file",
    default="pyproject.toml",
    show_default=True,
    help="Plugin loading file of your bot",
)
@click.argument("name", nargs=1, required=False)
def install(name, file, index):
    """Install nonebot plugin."""
    install_plugin(name, file, index)


@plugin.command()
@click.option("-i", "--index", default=None)
@click.argument("name", nargs=1)
def update(name, index):
    """Update nonebot plugin."""
    update_plugin(name, index)


@plugin.command(aliases=["remove"])
@click.option(
    "-f",
    "--file",
    default="pyproject.toml",
    show_default=True,
    help="Plugin loading file of your bot",
)
@click.argument("name", nargs=1)
def uninstall(name, file):
    uninstall_plugin(name, file)


@plugin.command(aliases=["create"])
@click.argument("name", required=False)
@click.option(
    "-d",
    "--plugin-dir",
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-T", "--template", default=None)
def new(name, plugin_dir, template):
    """Create a new nonebot plugin."""
    create_plugin(name, plugin_dir, template)
