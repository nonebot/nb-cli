import click

from nb_cli.utils import ClickAliasedCommand
from nb_cli.handlers import build_docker_image, run_docker_image, exit_docker_image


@click.command(cls=ClickAliasedCommand,
               context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def build(args):
    """Build Docker Image for Bot in Current Folder.
    The same as docker-compose build.
    
    Options see: https://docs.docker.com/compose/reference/build/
    """
    build_docker_image(args)


@click.command(
    cls=ClickAliasedCommand,
    aliases=["up"],  # type: ignore
    context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def deploy(args):
    """Build, Create, Start Containers for Bot in Current Folder.
    
    The same as docker-compose up -d.
    
    Options see: https://docs.docker.com/compose/reference/up/
    """
    run_docker_image(args)


@click.command(
    cls=ClickAliasedCommand,
    aliases=["down"],  # type: ignore
    context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def exit(args):
    """Stop and Remove Containers for Bot in Current Folder.
    
    The same as docker-compose down.
    
    Options see: https://docs.docker.com/compose/reference/down/
    """
    exit_docker_image(args)
