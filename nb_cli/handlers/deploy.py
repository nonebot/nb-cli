import os
import importlib
from typing import Iterable

import click
import nonebot

from ._docker import _call_docker_compose


def run_bot(file: str = "bot.py", app: str = "app"):
    if not os.path.isfile(file):
        click.secho(f"Cannot find {file} in current folder!", fg="red")
        return

    module_name, _ = os.path.splitext(file)
    module = importlib.import_module(module_name)
    _app = getattr(module, app, None)
    if not _app:
        nonebot.run()
    else:
        nonebot.run(app=f"{module_name}:{app}")


def build_docker_image(args: Iterable[str] = []):
    _call_docker_compose("build", args)


def run_docker_image(args: Iterable[str] = []):
    if "-d" not in args:
        args = ["-d", *args]
    _call_docker_compose("up", args)


def exit_docker_image(args: Iterable[str] = []):
    _call_docker_compose("down", args)
