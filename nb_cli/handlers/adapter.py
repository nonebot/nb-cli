from pathlib import Path
from typing import List, Optional

import httpx
import click
from PyInquirer import prompt
from cookiecutter.main import cookiecutter

from ._pip import _call_pip_install, _call_pip_update
from nb_cli.utils import Adapter, list_style, print_package_results


def create_adapter(name: Optional[str] = None,
                   adapter_dir: Optional[str] = None):
    if not name:
        question = [{
            "type": "input",
            "name": "adapter_name",
            "message": "Adapter Name:",
            "validate": lambda x: len(x) > 0
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "adapter_name" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        name = answers["adapter_name"]

    if not adapter_dir:
        detected = [
            str(x) for x in Path(".").glob("**/adapters/") if x.is_dir()
        ] or [
            f"{x}/adapters/" for x in Path(".").glob("*/") if x.is_dir() and
            not x.name.startswith(".") and not x.name.startswith("_")
        ]
        question = [{
            "type": "list",
            "name": "adapter_dir",
            "message": "Where to store the adapter?",
            "choices": detected + ["Other"],
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "adapter_dir" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        adapter_dir = answers["adapter_dir"]
        if adapter_dir == "Other":
            question = [{
                "type": "input",
                "name": "adapter_dir",
                "message": "Adapter Dir:",
                "validate": lambda x: len(x) > 0 and Path(x).is_dir()
            }]
            answers = prompt(question, qmark="[?]", style=list_style)
            if "adapter_dir" not in answers:
                click.secho(f"Error Input!", fg="red")
                return
            adapter_dir = answers["adapter_dir"]
    elif not Path(adapter_dir).is_dir():
        click.secho(f"Adapter Dir is not a directory!", fg="yellow")
        question = [{
            "type": "input",
            "name": "adapter_dir",
            "message": "Adapter Dir:",
            "validate": lambda x: len(x) > 0 and Path(x).is_dir()
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "adapter_dir" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        adapter_dir = answers["adapter_dir"]

    cookiecutter(str((Path(__file__).parent.parent / "adapter").resolve()),
                 no_input=True,
                 output_dir=adapter_dir,
                 extra_context={
                     "adapter_name": name,
                 })


def _get_adapter(package: Optional[str], question: str) -> Optional[Adapter]:
    _package: str
    if package is None:
        question_ = [{"type": "input", "name": "package", "message": question}]
        answers = prompt(question_, qmark="[?]", style=list_style)
        if not answers or "package" not in answers:
            click.secho("Error Input! Missing 'package'", fg="red")
            return
        _package = answers["package"]
    else:
        _package = package
    adapters = _get_adapters()
    adapter_exact = list(
        filter(
            lambda x: _package == x.id or _package == x.link or _package == x.
            name, adapters))
    if not adapter_exact:
        adapter = list(
            filter(
                lambda x: _package in x.id or _package in x.link or _package in
                x.name, adapters))
        if len(adapter) > 1:
            print_package_results(adapter)
            return
        elif len(adapter) != 1:
            click.secho("Package not found!", fg="red")
            return
        else:
            adapter = adapter[0]
    else:
        adapter = adapter_exact[0]
    return adapter


def search_adapter(package: Optional[str] = None):
    _package: str
    if package is None:
        question = [{
            "type": "input",
            "name": "package",
            "message": "Adapter name you want to search?"
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if not answers or "package" not in answers:
            click.secho("Error Input! Missing 'package'", fg="red")
            return
        _package = answers["package"]
    else:
        _package = package
    adapters = _get_adapters()
    adapters = list(
        filter(lambda x: any(_package in value for value in x.dict().values()),
               adapters))
    print_package_results(adapters)


def install_adapter(package: Optional[str] = None, index: Optional[str] = None):
    adapter = _get_adapter(package, "Adapter name you want to install?")
    if not adapter:
        return
    return _call_pip_install(adapter.link, index)


def update_adapter(package: Optional[str] = None, index: Optional[str] = None):
    adapter = _get_adapter(package, "Adapter name you want to update?")
    if not adapter:
        return
    return _call_pip_update(adapter.link, index)


def _get_adapters() -> List[Adapter]:
    res = httpx.get("https://v2.nonebot.dev/adapters.json")
    adapters = res.json()
    return list(map(lambda x: Adapter(**x), adapters))
