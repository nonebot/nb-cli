import sys
import click
import pkg_resources

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import search_plugin, create_plugin, update_plugin, install_plugin
from nb_cli.handlers import run_bot, create_project, handle_no_subcommand, _call_docker_compose

sys.path.insert(0, ".")

_dist = pkg_resources.get_distribution("nb-cli")
__version__ = _dist.version
VERSION = _dist.parsed_version


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.version_option(__version__,
                      "-V",
                      "--version",
                      message="%(prog)s: nonebot cli version %(version)s")
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        handle_no_subcommand()


@main.command(aliases=["create"])
def init():
    """Create A NoneBot Project."""
    create_project()


@main.command(aliases=["start"])
@click.option("-f",
              "--file",
              default="bot.py",
              show_default=True,
              help="Entry file of your bot")
@click.option("-a",
              "--app",
              default="app",
              show_default=True,
              help="ASGI application of your bot")
def run(file, app):
    """Run the Bot in Current Folder."""
    run_bot(file, app)


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def build(args):
    """Build Docker Image for Bot in Current Folder.
    The same as docker-compose build.
    
    Options see: https://docs.docker.com/compose/reference/build/
    """
    _call_docker_compose("build", args)


@main.command(aliases=["up"], context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def deploy(args):
    """Build, Create, Start Containers for Bot in Current Folder.
    
    The same as docker-compose up -d.
    
    Options see: https://docs.docker.com/compose/reference/up/
    """
    if "-d" not in args:
        args = ["-d", *args]
    _call_docker_compose("up", args)


@main.command(aliases=["down"],
              context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def exit(args):
    """Stop and Remove Containers for Bot in Current Folder.
    
    The same as docker-compose down.
    
    Options see: https://docs.docker.com/compose/reference/down/
    """
    _call_docker_compose("down", args)


@main.group(cls=ClickAliasedGroup)
def plugin():
    """Manage Bot Plugin."""
    pass


@plugin.command()
def list():
    """List nonebot plugin published on pypi."""
    search_plugin("")


@plugin.command()
@click.argument("name", nargs=1)
def search(name):
    """Search for nonebot plugin published on pypi."""
    search_plugin(name)


@plugin.command()
@click.option("-i", "--index", default="https://pypi.org/pypi")
@click.option("-f",
              "--file",
              default="bot.py",
              show_default=True,
              help="Entry file of your bot")
@click.argument("name", nargs=1)
def install(name, file, index):
    """Install nonebot plugin."""
    install_plugin(name, file, index)


@plugin.command()
@click.option("-i", "--index", default="https://pypi.org/pypi")
@click.argument("name", nargs=1)
def update(name, index):
    """Update nonebot plugin."""
    update_plugin(name, index)


@plugin.command(aliases=["create"])
@click.argument("name", required=False)
@click.option("-d",
              "--plugin-dir",
              type=click.Path(exists=True, file_okay=False, writable=True))
def new(name, plugin_dir):
    """Create a new nonebot plugin."""
    create_plugin(name, plugin_dir)


if __name__ == "__main__":
    main()
