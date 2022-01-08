from functools import partial
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
import httpx

from ._pip import _call_pip_install
from nb_cli.prompts import Choice, ListPrompt, InputPrompt
from nb_cli.utils import Driver, default_style, print_package_results


def _get_drivers() -> List[Driver]:
    urls = [
        "https://v2.nonebot.dev/drivers.json",
        "https://cdn.jsdelivr.net/gh/nonebot/nonebot2/website/static/drivers.json",
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(httpx.get, url) for url in urls]

        for future in as_completed(tasks):
            try:
                resp = future.result()
                drivers = resp.json()
                return list(map(lambda x: Driver(**x), drivers))
            except httpx.RequestError as e:
                click.secho(
                    f"An error occurred while requesting {e.request.url}.",
                    fg="red",
                )

    raise RuntimeError("Failed to get plugin list.")


def _get_driver(name: Optional[str], question: str) -> Optional[Driver]:
    _name: str
    if name is None:
        _name = InputPrompt(question).prompt(style=default_style)
    else:
        _name = name
    drivers = _get_drivers()
    driver_exact = list(
        filter(
            lambda x: _name == x.module_name
            or _name == x.project_link
            or _name == x.name,
            drivers,
        )
    )
    if not driver_exact:
        driver = list(
            filter(
                lambda x: _name in x.module_name
                or _name in x.project_link
                or _name in x.name,
                drivers,
            )
        )
        if len(driver) > 1:
            print_package_results(driver)
            return
        elif len(driver) != 1:
            click.secho("Package not found!", fg="red")
            return
        else:
            driver = driver[0]
    else:
        driver = driver_exact[0]
    return driver


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
            lambda x: any(_name in value for value in x.dict().values()),
            drivers,
        )
    )
    print_package_results(drivers)
    return True


def install_driver(
    name: Optional[str] = None, index: Optional[str] = None
) -> bool:
    driver = _get_driver(name, "Driver name you want to install?")
    if not driver:
        return True
    if driver.project_link:
        _call_pip_install(f"nonebot2[{driver.project_link}]", index)
    return True
