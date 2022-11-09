import os
from typing import List, Callable, Iterable

from noneprompt import Choice, ListPrompt

from nb_cli.utils import default_style
from nb_cli.config import ConfigManager
from nb_cli.loader import NoneBotProcess
from nb_cli.loader.reloader import WatchFilesReload

from ._docker import _call_docker_compose


def run_bot(script: str = "bot.py", file: str = "pyproject.toml") -> bool:
    config = ConfigManager.get_local_config(file)

    if os.path.isfile(script):
        process = NoneBotProcess(config, script)
    else:
        process = NoneBotProcess(config)

    if config.get("reload"):
        WatchFilesReload(config, process).run()
    else:
        process.run()

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
