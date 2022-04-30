from functools import partial
from typing import List, Callable, Optional

from nb_cli.prompts import Choice, ListPrompt

from ._pip import _call_pip_install
from .utils import (
    Driver,
    _get_module,
    _get_modules,
    default_style,
    _search_module,
)


def _get_drivers() -> List[Driver]:
    return _get_modules(Driver)


def _get_driver(name: Optional[str], question: str) -> Optional[Driver]:
    return _get_module(Driver, name, question)


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
    return _search_module(Driver, name)


def install_driver(
    name: Optional[str] = None, index: Optional[str] = None
) -> bool:
    driver = _get_driver(name, "Driver name you want to install?")
    if not driver:
        return True
    if driver.project_link:
        _call_pip_install(f"nonebot2[{driver.project_link}]", index)
    return True
