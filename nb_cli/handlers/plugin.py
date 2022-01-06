from pathlib import Path
from functools import partial
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
import httpx
from cookiecutter.main import cookiecutter

from ._config import JSONConfig, TOMLConfig
from nb_cli.utils import Plugin, default_style, print_package_results
from nb_cli.prompts import Choice, ListPrompt, InputPrompt, ConfirmPrompt
from ._pip import _call_pip_update, _call_pip_install, _call_pip_uninstall


def plugin_no_subcommand(add_back: bool = False) -> bool:
    choices: List[Choice[Callable[[], bool]]] = [
        Choice("Create a New NoneBot Plugin", create_plugin),
        Choice("List All Published Plugins", partial(search_plugin, "")),
        Choice("Search for Published Plugin", search_plugin),
        Choice("Install a Published Plugin", install_plugin),
        Choice("Update a Published Plugin", update_plugin),
        Choice("Remove an Installed Plugin", uninstall_plugin),
    ]
    if add_back:
        choices.append(Choice("<- Back", lambda: False))
    subcommand = (
        ListPrompt("What do you want to do?", choices)
        .prompt(style=default_style)
        .data
    )
    return subcommand()


def create_plugin(
    name: Optional[str] = None,
    plugin_dir: Optional[str] = None,
    template: Optional[str] = None,
) -> bool:
    if not name:
        name = InputPrompt(
            "Plugin Name:", validator=lambda x: len(x) > 0
        ).prompt(style=default_style)

    if not plugin_dir:
        detected: List[Choice[None]] = [
            Choice(str(x)) for x in Path(".").glob("**/plugins/") if x.is_dir()
        ]
        plugin_dir = (
            ListPrompt(
                "Where to store the plugin?", detected + [Choice("Other")]
            )
            .prompt(style=default_style)
            .name
        )
        if plugin_dir == "Other":
            plugin_dir = InputPrompt(
                "Plugin Dir:",
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
            ).prompt(style=default_style)
    elif not Path(plugin_dir).is_dir():
        click.secho(f"Plugin Dir is not a directory!", fg="yellow")
        plugin_dir = InputPrompt(
            "Plugin Dir:", validator=lambda x: len(x) > 0 and Path(x).is_dir()
        ).prompt(style=default_style)
    if not template:
        sub_plugin = ConfirmPrompt(
            "Do you want to load sub plugins in current plugin?",
            default_choice=False,
        ).prompt(style=default_style)
        cookiecutter(
            str((Path(__file__).parent.parent / "plugin").resolve()),
            no_input=True,
            output_dir=plugin_dir,
            extra_context={"plugin_name": name, "sub_plugin": sub_plugin},
        )
    else:
        cookiecutter(
            template, output_dir=plugin_dir, extra_context={"plugin_name": name}
        )
    return True


def _get_plugin(package: Optional[str], question: str) -> Optional[Plugin]:
    _package: str
    if package is None:
        _package = InputPrompt(question).prompt(style=default_style)
    else:
        _package = package
    plugins = _get_plugins()
    plugin_exact = list(
        filter(
            lambda x: _package == x.module_name
            or _package == x.project_link
            or _package == x.name,
            plugins,
        )
    )
    if not plugin_exact:
        plugin = list(
            filter(
                lambda x: _package in x.module_name
                or _package in x.project_link
                or _package in x.name,
                plugins,
            )
        )
        if len(plugin) > 1:
            print_package_results(plugin)
            return
        elif len(plugin) != 1:
            click.secho("Package not found!", fg="red")
            return
        else:
            plugin = plugin[0]
    else:
        plugin = plugin_exact[0]
    return plugin


def search_plugin(package: Optional[str] = None) -> bool:
    _package: str
    if package is None:
        _package = InputPrompt("Plugin name you want to search?").prompt(
            style=default_style
        )
    else:
        _package = package
    plugins = _get_plugins()
    plugins = list(
        filter(
            lambda x: any(_package in value for value in x.dict().values()),
            plugins,
        )
    )
    print_package_results(plugins)
    return True


def install_plugin(
    package: Optional[str] = None,
    file: str = "pyproject.toml",
    index: Optional[str] = None,
) -> bool:
    plugin = _get_plugin(package, "Plugin name you want to install?")
    if not plugin:
        return True
    status = _call_pip_install(plugin.project_link, index)
    if status == 0:  # SUCCESS
        try:
            if Path(file).suffix == ".toml":
                config = TOMLConfig(file)
            elif Path(file).suffix == ".json":
                config = JSONConfig(file)
            else:
                raise ValueError(
                    "Unknown config file format! Expect 'json' / 'toml'."
                )
            config.add_plugin(plugin.module_name)
        except Exception as e:
            click.secho(repr(e), fg="red")
    return True


def update_plugin(
    package: Optional[str] = None, index: Optional[str] = None
) -> bool:
    plugin = _get_plugin(package, "Plugin name you want to update?")
    if plugin:
        _call_pip_update(plugin.project_link, index)
    return True


def uninstall_plugin(
    package: Optional[str] = None, file: str = "pyproject.toml"
) -> bool:
    plugin = _get_plugin(package, "Plugin name you want to uninstall?")
    if not plugin:
        return True
    status = _call_pip_uninstall(plugin.project_link)
    if status == 0:  # SUCCESS
        try:
            if Path(file).suffix == ".toml":
                config = TOMLConfig(file)
            elif Path(file).suffix == ".json":
                config = JSONConfig(file)
            else:
                raise ValueError(
                    "Unknown config file format! Expect 'json' / 'toml'."
                )
            config.remove_plugin(plugin.module_name)
        except Exception as e:
            click.secho(repr(e), fg="red")
    return True


def _get_plugins() -> List[Plugin]:
    urls = [
        "https://v2.nonebot.dev/plugins.json",
        "https://cdn.jsdelivr.net/gh/nonebot/nonebot2/website/static/plugins.json",
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [executor.submit(httpx.get, url) for url in urls]

        for future in as_completed(tasks):
            try:
                resp = future.result()
                plugins = resp.json()
                return list(map(lambda x: Plugin(**x), plugins))
            except httpx.RequestError as e:
                click.secho(
                    f"An error occurred while requesting {e.request.url}.",
                    fg="red",
                )

    raise RuntimeError("Failed to get plugin list.")
