import sys
import json
import subprocess
from functools import partial
from typing import List, Literal, Callable

import click
from noneprompt import Choice, ListPrompt

from nb_cli.config import Config
from nb_cli.utils import default_style
from nb_cli.consts import CONFIG_KEY, GET_SCRIPTS_SCRIPT, RUN_SCRIPTS_SCRIPT

from .utils import gen_load_script


def script_no_subcommand(ctx: click.Context) -> bool:
    config: Config = ctx.meta[CONFIG_KEY]
    scripts = list_scripts(config.nb_cli.python)
    choices: List[Choice[Callable[[], bool]]] = [
        Choice(
            f"Run script {script!r}",
            partial(run_script, script_name=script, config=config),
        )
        for script in scripts
    ]
    choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def list_scripts(python_path: str = "python") -> List[str]:
    output = subprocess.check_output(
        [python_path, "-W", "ignore", "-c", GET_SCRIPTS_SCRIPT], text=True
    )
    return json.loads(output)


def run_script(script_name: str, config: Config) -> Literal[True]:
    subprocess.run(
        [
            config.nb_cli.python,
            "-W",
            "ignore",
            "-c",
            RUN_SCRIPTS_SCRIPT.format(
                preload_bot=gen_load_script(config), script_name=script_name
            ),
        ],
        check=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return True
