from typing import List
from pathlib import Path

import click
from cookiecutter.main import cookiecutter

from .adapter import _get_adapters
from ._pip import _call_pip_install
from nb_cli.utils import default_style
from nb_cli.prompts import Choice, ListPrompt, InputPrompt, ConfirmPrompt, CheckboxPrompt


def create_project():
    click.secho("Loading adapters...")
    adapters = {x.name: x for x in _get_adapters()}
    click.clear()
    answers = {}

    answers["project_name"] = InputPrompt(
        "Project Name:",
        validator=lambda x: len(x) > 0).prompt(style=default_style)

    dir_name = answers["project_name"].lower().replace(" ",
                                                       "-").replace("-", "_")
    src_choices: List[Choice[bool]] = [
        Choice(f"1) In a \"{dir_name}\" folder", False),
        Choice("2) In a \"src\" folder", True)
    ]
    answers["use_src"] = ListPrompt(
        "Where to store the plugin?",
        src_choices).prompt(style=default_style).data

    answers["load_builtin"] = ConfirmPrompt(
        "Load NoneBot Builtin Plugin?",
        default_choice=False).prompt(style=default_style)

    answers["adapters"] = {"builtin": []}

    confirm = False
    while not confirm:
        answers["adapters"]["builtin"] = [
            choice.data.dict() for choice in CheckboxPrompt(
                "Which adapter(s) would you like to use?",
                [Choice(name, adapter)
                 for name, adapter in adapters.items()]).prompt(
                     style=default_style)
        ]
        if not answers["adapters"]["builtin"]:
            confirm = ConfirmPrompt(
                "You haven't chosen any adapter. Please confirm.",
                default_choice=False).prompt(style=default_style)
        else:
            confirm = True
    cookiecutter(str((Path(__file__).parent.parent / "project").resolve()),
                 no_input=True,
                 extra_context=answers)

    for adapter in answers["adapters"]["builtin"]:
        _call_pip_install(adapter["link"])
