from pathlib import Path
from typing import List, Optional

import httpx
import click
from cookiecutter.main import cookiecutter
from concurrent.futures import ThreadPoolExecutor, as_completed

from ._pip import _call_pip_install, _call_pip_update
from nb_cli.prompts import Choice, ListPrompt, InputPrompt
from nb_cli.utils import Adapter, default_style, print_package_results


def create_adapter(name: Optional[str] = None,
                   adapter_dir: Optional[str] = None):
    if not name:
        name = InputPrompt(
            "Adapter Name:",
            validator=lambda x: len(x) > 0).prompt(style=default_style)

    if not adapter_dir:
        detected: List[Choice[None]] = [
            Choice(str(x))
            for x in Path(".").glob("**/adapters/")
            if x.is_dir()
        ] or [
            Choice(f"{x}/adapters/")
            for x in Path(".").glob("*/")
            if x.is_dir() and not x.name.startswith(".") and
            not x.name.startswith("_")
        ]
        adapter_dir = ListPrompt(
            "Where to store the adapter?",
            detected + [Choice("Other")]).prompt(style=default_style).name
        if adapter_dir == "Other":
            adapter_dir = InputPrompt(
                "Adapter Dir:",
                validator=lambda x: len(x) > 0 and Path(x).is_dir()).prompt(
                    style=default_style)
    elif not Path(adapter_dir).is_dir():
        click.secho(f"Adapter Dir is not a directory!", fg="yellow")
        adapter_dir = InputPrompt(
            "Adapter Dir:",
            validator=lambda x: len(x) > 0 and Path(x).is_dir()).prompt(
                style=default_style)

    cookiecutter(str((Path(__file__).parent.parent / "adapter").resolve()),
                 no_input=True,
                 output_dir=adapter_dir,
                 extra_context={
                     "adapter_name": name,
                 })


def _get_adapter(package: Optional[str], question: str) -> Optional[Adapter]:
    _package: str
    if package is None:
        _package = InputPrompt(question).prompt(style=default_style)
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
        _package = InputPrompt("Adapter name you want to search?").prompt(
            style=default_style)
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
    urls = [
        "https://v2.nonebot.dev/adapters.json",
        "https://nonebot2-vercel-mirror.vercel.app/adapters.json",
        "https://cdn.jsdelivr.net/gh/nonebot/nonebot2/docs/.vuepress/public/adapters.json"
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(httpx.get, url) for url in urls]

        for future in as_completed(tasks):
            try:
                resp = future.result()
                adapters = resp.json()
                return list(map(lambda x: Adapter(**x), adapters))
            except httpx.RequestError as e:
                click.secho(
                    f"An error occurred while requesting {e.request.url}.",
                    fg="red")

    raise RuntimeError("Failed to get adapter list.")
