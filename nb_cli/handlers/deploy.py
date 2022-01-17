import os
import importlib
from typing import List, Callable, Iterable

import click
import nonebot

from nb_cli.utils import default_style
from ._docker import _call_docker_compose
from nb_cli.prompts import Choice, ListPrompt


def run_bot(file: str = "bot.py", app: str = "app") -> bool:
    if not os.path.isfile(file):
        click.secho(f"Cannot find {file} in current folder!", fg="red")
        return True

    module_name, _ = os.path.splitext(file)
    module = importlib.import_module(module_name)
    _app = getattr(module, app, None)
    if not _app:
        nonebot.run()
    else:
        nonebot.run(app=f"{module_name}:{app}")
    return True


def deploy_no_subcommand(add_back: bool = False) -> bool:
    choices: List[Choice[Callable[[], bool]]] = [
        Choice("Build Docker Image for the Bot", build_docker_image),
        Choice("Deploy the Bot to Docker", run_docker_image),
        Choice("Stop the Bot Container in Docker", exit_docker_image),
    ]
    if add_back:
        choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def build_docker_image(args: Iterable[str] = []) -> bool:
    _call_docker_compose("build", args)
    return True


def run_docker_image(args: Iterable[str] = []) -> bool:
    if "-d" not in args:
        args = ["-d", *args]
    _call_docker_compose("up", args)
    return True


def exit_docker_image(args: Iterable[str] = []) -> bool:
    _call_docker_compose("down", args)
    return True
