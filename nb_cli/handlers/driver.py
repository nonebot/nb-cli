from functools import partial
from typing import List, Callable, Optional

import click
import pkg_resources

from ._pip import _call_pip_install
from nb_cli.utils import default_style
from nb_cli.prompts import Choice, ListPrompt, InputPrompt


def _get_drivers() -> List[str]:
    dist = pkg_resources.get_distribution("nonebot2")
    return dist.extras


def _get_driver(name: Optional[str], question: str) -> Optional[str]:
    _name: str
    if name is None:
        _name = InputPrompt(question).prompt(style=default_style)
    else:
        _name = name
    drivers = _get_drivers()
    if _name not in drivers:
        click.secho("Package not found!", fg="red")
        return
    return _name


def driver_no_subcommand(add_back: bool = False) -> bool:
    choices: List[Choice[Callable[[], bool]]] = [
        Choice("List All Builtin Drivers", partial(search_driver, "")),
        Choice("Search for Builtin Driver", search_driver),
        Choice("Install a Builtin Driver", install_driver),
    ]
    if add_back:
        choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def search_driver(name: Optional[str] = None) -> bool:
    _name: str
    if name is None:
        _name = InputPrompt("Plugin name you want to search?").prompt(
            style=default_style
        )
    else:
        _name = name
    drivers = _get_drivers()
    drivers = list(
        filter(
            lambda x: any(_name in value for value in x),
            drivers,
        )
    )
    click.echo("\n".join(drivers))
    return True


def install_driver(
    name: Optional[str] = None, index: Optional[str] = None
) -> bool:
    driver = _get_driver(name, "Driver name you want to install?")
    if not driver:
        return True
    _call_pip_install(f"nonebot2[{driver}]", index)
    return True
