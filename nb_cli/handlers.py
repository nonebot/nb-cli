#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from PyInquirer import prompt
from pyfiglet import figlet_format

from nb_cli.utils import list_style


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def create_project():
    pass


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    choices = {"Show Logo": draw_logo, "Create a New Project": create_project}
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
