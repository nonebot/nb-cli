from typing import List, TypeVar, Optional

import click
from noneprompt import InputPrompt

from nb_cli.cli import CLI_DEFAULT_STYLE
from nb_cli.config import Driver, Plugin, Adapter
from nb_cli.handlers import print_package_results

T = TypeVar("T", Adapter, Plugin, Driver)


def find_exact_package(question: str, name: Optional[str], packages: List[T]) -> T:
    if name is None:
        name = InputPrompt(question).prompt(style=CLI_DEFAULT_STYLE)

    if exact_packages := [
        p for p in packages if name in {p.name, p.module_name, p.project_link}
    ]:
        return exact_packages[0]

    packages = [
        p
        for p in packages
        if name in p.name or name in p.module_name or name in p.project_link
    ]
    if len(packages) == 1:
        return packages[0]
    if len(packages) > 1:
        print_package_results(packages)
    else:
        click.echo(f"Package {name} not found.")

    click.get_current_context().exit(1)
