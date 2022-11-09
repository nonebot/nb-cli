import sys
from typing import List, Callable, Optional

from noneprompt import Choice, ListPrompt, InputPrompt

from nb_cli.utils import default_style

from ._pip import _call_pip_update, _call_pip_install, _call_pip_uninstall


def self_no_subcommand(add_back: bool = False) -> bool:
    choices: List[Choice[Callable[[], bool]]] = [
        Choice("Update CLI", self_update),
        Choice("Install a Package to CLI's venv", self_install),
        Choice("Remove a Package from CLI's venv", self_uninstall),
    ]
    if add_back:
        choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def self_update(
    index: Optional[str] = None,
) -> bool:

    status = _call_pip_update("nb-cli", index, sys.executable)
    return True


def self_install(
    package: Optional[str] = None, index: Optional[str] = None
) -> bool:
    _package: str = ""
    if not package:
        _package = InputPrompt("Package name you want to install?").prompt(
            style=default_style
        )
    else:
        _package = package

    status = _call_pip_install(_package, index, sys.executable)
    return True


def self_uninstall(package: Optional[str] = None) -> bool:
    _package: str = ""
    if not package:
        _package = InputPrompt("Package name you want to uninstall?").prompt(
            style=default_style
        )
    else:
        _package = package

    status = _call_pip_uninstall(_package, sys.executable)
    return True
