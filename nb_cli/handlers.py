#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib
from pathlib import Path

import click
import nonebot
from cookiecutter.main import cookiecutter
from PyInquirer import prompt
from pyfiglet import figlet_format

from nb_cli.utils import list_style


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def run_bot(file="bot.py", app="app"):
    if not os.path.isfile(file):
        click.secho(f"Cannot find {file} in current folder!", fg="red")
        return

    module = importlib.import_module("bot")
    _app = getattr(module, app)
    if not _app:
        click.secho(
            "Cannot find an asgi server. Add `app = nonebot.get_asgi()` to enable reload mode."
        )
        nonebot.run()
    else:
        nonebot.run(app="bot:app")


def create_project():
    question = [{
        "type": "input",
        "name": "project_name",
        "message": "Project Name:",
        "validate": lambda x: len(x) > 0
    }, {
        "type": "list",
        "name": "license",
        "message": "License:",
        "choices": [
            "MIT", "Apache-2.0", "GPL-3.0-only", "BSD-3-Clause",
            "Create Your Self"
        ],
        "filter": lambda x: "" if x == "Create Your Self" else x
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
        "Show Logo": draw_logo,
        "Create a New Project": create_project,
        "Run the Bot in Current Folder": run_bot
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
