#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Iterable
from functools import partial

try:
    from pip._internal.cli.main import main as pipmain
except ImportError:
    from pip import main as pipmain

import click
import nonebot
from PyInquirer import prompt
from pyfiglet import figlet_format
from cookiecutter.main import cookiecutter
from compose.cli.main import TopLevelCommand, DocoptDispatcher, project_from_options, perform_command
from compose.cli.main import setup_console_handler, setup_parallel_logger, set_no_color_if_clicolor

from nb_cli.utils import list_style


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def run_bot(file: str = "bot.py", app: str = "app"):
    if not os.path.isfile(file):
        click.secho(f"Cannot find {file} in current folder!", fg="red")
        return

    module_name, _ = os.path.splitext(file)
    module = importlib.import_module(module_name)
    _app = getattr(module, app)
    if not _app:
        click.secho(
            "Cannot find an asgi server. Add `app = nonebot.get_asgi()` to enable reload mode."
        )
        nonebot.run()
    else:
        nonebot.run(app=f"{module_name}:{app}")


def create_project():
    question = [{
        "type": "input",
        "name": "project_name",
        "message": "Project Name:",
        "validate": lambda x: len(x) > 0
    }, {
        "type":
            "list",
        "name":
            "use_src",
        "message":
            "Where to store the plugin?",
        "choices":
            lambda ctx: [
                f"1) In a \"{ctx['project_name'].lower().replace(' ', '-').replace('-', '_')}\" folder",
                "2) In a \"src\" folder"
            ],
        "filter":
            lambda x: x.startswith("2")
    }, {
        "type": "confirm",
        "name": "load_builtin",
        "message": "Load NoneBot Builtin Plugin?",
        "default": False
    }]
    keys = set(map(lambda x: x["name"], question))
    answers = prompt(question, qmark="[?]", style=list_style)
    if keys != set(answers.keys()):
        click.secho(f"Error Input! Missing {list(keys - set(answers.keys()))}",
                    fg="red")
        return
    cookiecutter(str(Path(__file__).parent.resolve()),
                 no_input=True,
                 extra_context=answers)


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    choices = {
        "Show Logo":
            draw_logo,
        "Create a New Project":
            create_project,
        "Run the Bot in Current Folder":
            run_bot,
        "Build Docker Image for the Bot":
            partial(_call_docker_compose, "build", []),
        "Deploy the Bot to Docker":
            partial(_call_docker_compose, "up", ["-d"]),
        "Stop the Bot Container in Docker":
            partial(_call_docker_compose, "down")
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


def _call_docker_compose(command: str, args: Iterable[str]):
    dispatcher = DocoptDispatcher(TopLevelCommand, {"options_first": True})
    options, handler, command_options = dispatcher.parse([command, *args])
    setup_console_handler(logging.StreamHandler(sys.stderr),
                          options.get('--verbose'),
                          set_no_color_if_clicolor(options.get('--no-ansi')),
                          options.get("--log-level"))
    setup_parallel_logger(set_no_color_if_clicolor(options.get('--no-ansi')))
    if options.get('--no-ansi'):
        command_options['--no-color'] = True
    return perform_command(options, handler, command_options)


def _call_pip(command: str, *args: str):
    return pipmain([command, *args])
