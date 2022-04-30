from pathlib import Path
from functools import partial
from typing import List, Callable, Optional

import click
from cookiecutter.main import cookiecutter

from nb_cli.prompts import Choice, ListPrompt, InputPrompt

from ._pip import _call_pip_update, _call_pip_install
from .utils import (
    Adapter,
    _get_module,
    _get_modules,
    default_style,
    _search_module,
)


def adapter_no_subcommand(add_back: bool = False) -> bool:
    choices: List[Choice[Callable[[], bool]]] = [
        Choice("Create a Custom Adapter", create_adapter),
        Choice("List All Published Adapters", partial(search_adapter, "")),
        Choice("Search for Published Adapters", search_adapter),
        Choice("Install a Published Adapter", install_adapter),
    ]
    if add_back:
        choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def create_adapter(
    name: Optional[str] = None, adapter_dir: Optional[str] = None
) -> bool:
    if not name:
        name = InputPrompt(
            "Adapter Name:", validator=lambda x: len(x) > 0
        ).prompt(style=default_style)

    if not adapter_dir:
        detected: List[Choice[None]] = [
            Choice(str(x)) for x in Path(".").glob("**/adapters/") if x.is_dir()
        ] or [
            Choice(f"{x}/adapters/")
            for x in Path(".").glob("*/")
            if x.is_dir()
            and not x.name.startswith(".")
            and not x.name.startswith("_")
        ]
        adapter_dir = (
            ListPrompt(
                "Where to store the adapter?", detected + [Choice("Other")]
            )
            .prompt(style=default_style)
            .name
        )
        if adapter_dir == "Other":
            adapter_dir = InputPrompt(
                "Adapter Dir:",
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
            ).prompt(style=default_style)
    elif not Path(adapter_dir).is_dir():
        click.secho(f"Adapter Dir is not a directory!", fg="yellow")
        adapter_dir = InputPrompt(
            "Adapter Dir:", validator=lambda x: len(x) > 0 and Path(x).is_dir()
        ).prompt(style=default_style)

    cookiecutter(
        str((Path(__file__).parent.parent / "adapter").resolve()),
        no_input=True,
        output_dir=adapter_dir,
        extra_context={
            "adapter_name": name,
        },
    )
    return True


def _get_adapter(package: Optional[str], question: str) -> Optional[Adapter]:
    return _get_module(Adapter, package, question)


def search_adapter(package: Optional[str] = None) -> bool:
    return _search_module(Adapter, package)


def install_adapter(
    package: Optional[str] = None, index: Optional[str] = None
) -> bool:
    adapter = _get_adapter(package, "Adapter name you want to install?")
    if adapter:
        _call_pip_install(adapter.project_link, index)
    return True


def update_adapter(
    package: Optional[str] = None, index: Optional[str] = None
) -> bool:
    adapter = _get_adapter(package, "Adapter name you want to update?")
    if adapter:
        _call_pip_update(adapter.project_link, index)
    return True


def _get_adapters() -> List[Adapter]:
    return _get_modules(Adapter)
