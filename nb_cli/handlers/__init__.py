from functools import partial

import click
from PyInquirer import prompt
from pyfiglet import figlet_format

from nb_cli.utils import list_style

from .project import create_project
from .deploy import run_bot, build_docker_image, run_docker_image, exit_docker_image
from .adapter import create_adapter, search_adapter
from .plugin import create_plugin, search_plugin, install_plugin, update_plugin, uninstall_plugin


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    choices = {
        "Show Logo": draw_logo,
        "Create a New Project": create_project,
        "Run the Bot in Current Folder": run_bot,
        "Create a New NoneBot Plugin": create_plugin,
        "List All Published Plugins": partial(search_plugin, ""),
        "Search for Published Plugin": search_plugin,
        "Install a Published Plugin": install_plugin,
        "Update a Published Plugin": update_plugin,
        "Remove an Installed Plugin": uninstall_plugin,
        "Create a Custom Adapter": create_adapter,
        "List All Published Adapters": partial(search_adapter, ""),
        "Search for Published Adapters": search_adapter,
        "Build Docker Image for the Bot": build_docker_image,
        "Deploy the Bot to Docker": run_docker_image,
        "Stop the Bot Container in Docker": exit_docker_image,
    }
    question = [{
        "type": "list",
        "name": "subcommand",
        "message": "What do you want to do?",
        "choices": choices.keys(),
        "filter": lambda x: choices[x]
    }]
    answers = prompt(question, style=list_style)
    if "subcommand" not in answers or not answers["subcommand"]:
        click.secho("Error Input!", fg="red")
        return
    answers["subcommand"]()
