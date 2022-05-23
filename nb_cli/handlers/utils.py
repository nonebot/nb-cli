import shutil
from typing import List, Type, Union, TypeVar, Optional, cast
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
import httpx
from wcwidth import wcswidth
from pydantic import BaseModel

from nb_cli.prompts import InputPrompt
from nb_cli.utils import default_style

T = TypeVar("T", "Adapter", "Plugin", "Driver")


class Adapter(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


class Plugin(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


class Driver(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


def print_package_results(
    hits: List[T],
    name_column_width: Optional[int] = None,
    terminal_width: Optional[int] = None,
):
    if not hits:
        return

    if name_column_width is None:
        name_column_width = cast(
            int,
            (
                max(
                    [
                        wcswidth(f"{hit.name} ({hit.project_link})")
                        for hit in hits
                    ]
                )
                + 4
            ),
        )
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size()[0]

    for hit in hits:
        name = f"{hit.name} ({hit.project_link})"
        summary = hit.desc
        target_width = terminal_width - name_column_width - 5
        if target_width > 10:
            # wrap and indent summary to fit terminal
            summary_lines = []
            while wcswidth(summary) > target_width:
                tmp_length = target_width
                while wcswidth(summary[:tmp_length]) > target_width:
                    tmp_length = tmp_length - 1
                summary_lines.append(summary[:tmp_length])
                summary = summary[tmp_length:]
            summary_lines.append(summary)
            summary = ("\n" + " " * (name_column_width + 3)).join(summary_lines)

        line = (
            f"{name + ' ' * (name_column_width - wcswidth(name))} - {summary}"
        )
        try:
            print(line)
        except UnicodeEncodeError:
            pass


def _get_modules(module_type: Type[T]) -> List[T]:
    module_name = module_type.__name__.lower()

    urls = [
        f"https://v2.nonebot.dev/{module_name}s.json",
        f"https://fastly.jsdelivr.net/gh/nonebot/nonebot2/website/static/{module_name}s.json",
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(httpx.get, url) for url in urls]

        for future in as_completed(tasks):
            try:
                resp = future.result()
                items = resp.json()
                return list(map(lambda x: module_type(**x), items))
            except httpx.RequestError as e:
                click.secho(
                    f"An error occurred while requesting {e.request.url}.",
                    fg="red",
                )

    raise RuntimeError(f"Failed to get {module_name} list.")


def _get_module(
    module_type: Type[T], package: Optional[str], question: str
) -> Optional[T]:
    _package: str
    if package is None:
        _package = InputPrompt(question).prompt(style=default_style)
    else:
        _package = package
    modules = _get_modules(module_type)
    modules_exact = list(
        filter(
            lambda x: _package == x.module_name
            or _package == x.project_link
            or _package == x.name,
            modules,
        )
    )
    if not modules_exact:
        module = list(
            filter(
                lambda x: _package in x.module_name
                or _package in x.project_link
                or _package in x.name,
                modules,
            )
        )
        if len(module) > 1:
            print_package_results(module)
            return
        elif len(module) != 1:
            click.secho("Package not found!", fg="red")
            return
        else:
            module = module[0]
    else:
        module = modules_exact[0]
    return module


def _search_module(module_type: Type[T], package: Optional[str] = None) -> bool:
    _package: str
    if package is None:
        _package = InputPrompt("Adapter name you want to search?").prompt(
            style=default_style
        )
    else:
        _package = package
    modules = _get_modules(module_type)
    modules = list(
        filter(
            lambda x: any(_package in value for value in x.dict().values()),
            modules,
        )
    )
    print_package_results(modules)
    return True
