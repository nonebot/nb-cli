from functools import partial
from typing import Any, List, Callable

import click
from pyfiglet import figlet_format

from .project import create_project
from .deploy import run_bot as run_bot
from nb_cli.utils import default_style
from nb_cli.prompts import Choice, ListPrompt
from .driver import search_driver as search_driver
from .plugin import create_plugin as create_plugin
from .plugin import search_plugin as search_plugin
from .plugin import update_plugin as update_plugin
from .driver import install_driver as install_driver
from .plugin import install_plugin as install_plugin
from .adapter import create_adapter as create_adapter
from .adapter import search_adapter as search_adapter
from .adapter import update_adapter as update_adapter
from .adapter import install_adapter as install_adapter
from .deploy import run_docker_image as run_docker_image
from .plugin import uninstall_plugin as uninstall_plugin
from .deploy import exit_docker_image as exit_docker_image
from .deploy import build_docker_image as build_docker_image
from .deploy import deploy_no_subcommand as deploy_no_subcommand
from .driver import driver_no_subcommand as driver_no_subcommand
from .plugin import plugin_no_subcommand as plugin_no_subcommand
from .adapter import adapter_no_subcommand as adapter_no_subcommand


def draw_logo() -> bool:
    click.secho(
        figlet_format("NoneBot", font="basic").strip(), fg="cyan", bold=True
    )
    return True


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    while True:
        choices: List[Choice[Callable[[], bool]]] = [
            Choice("Show Logo", draw_logo),
            Choice("Create a New Project", create_project),
            Choice("Run the Bot in Current Folder", run_bot),
            Choice("Driver ->", partial(driver_no_subcommand, True)),
            Choice("Plugin ->", partial(plugin_no_subcommand, True)),
            Choice("Adapter ->", partial(adapter_no_subcommand, True)),
            Choice("Deploy ->", partial(deploy_no_subcommand, True)),
        ]
        subcommand = (
            ListPrompt("What do you want to do?", choices)
            .prompt(style=default_style)
            .data
        )
        result = subcommand()
        if result:
            break
