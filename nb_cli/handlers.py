#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib

import click
import nonebot
from PyInquirer import prompt
from pyfiglet import figlet_format

from nb_cli.utils import list_style


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def run_bot():
    if not os.path.isfile("bot.py"):
        click.secho("Cannot find a bot.py file in current folder!", fg="red")
        return

    module = importlib.import_module("bot")
    app = getattr(module, "app")
    if not app:
        click.secho(
            "Cannot find an asgi server. Add `app = nonebot.get_asgi()` to enable reload mode."
        )
        nonebot.run()
    else:
        nonebot.run(app="bot:app")


def create_project():
    pass


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
        return
    answers["subcommand"]()
