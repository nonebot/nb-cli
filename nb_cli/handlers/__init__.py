from functools import partial

import click
from typing import Any, List, Callable
from pyfiglet import figlet_format

from nb_cli.utils import default_style
from nb_cli.prompts import Choice, ListPrompt

from .project import create_project
from .deploy import run_bot, build_docker_image, run_docker_image, exit_docker_image
from .adapter import create_adapter, search_adapter, install_adapter, update_adapter
from .plugin import create_plugin, search_plugin, install_plugin, update_plugin, uninstall_plugin


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    choices: List[Choice[Callable[[], Any]]] = [
        Choice("Show Logo", draw_logo),
        Choice("Create a New Project", create_project),
        Choice("Run the Bot in Current Folder", run_bot),
        Choice("Create a New NoneBot Plugin", create_plugin),
        Choice("List All Published Plugins", partial(search_plugin, "")),
        Choice("Search for Published Plugin", search_plugin),
        Choice("Install a Published Plugin", install_plugin),
        Choice("Update a Published Plugin", update_plugin),
        Choice("Remove an Installed Plugin", uninstall_plugin),
        Choice("Create a Custom Adapter", create_adapter),
        Choice("List All Published Adapters", partial(search_adapter, "")),
        Choice("Search for Published Adapters", search_adapter),
        Choice("Build Docker Image for the Bot", build_docker_image),
        Choice("Deploy the Bot to Docker", run_docker_image),
        Choice("Stop the Bot Container in Docker", exit_docker_image),
    ]
    subcommand = ListPrompt("What do you want to do?",
                            choices).prompt(style=default_style).data
    subcommand()
