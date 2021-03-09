import os
from pathlib import Path
from typing import List, Optional

import httpx
import click
from PyInquirer import prompt
from cookiecutter.main import cookiecutter

from ._config import TOMLConfig, JSONConfig
from nb_cli.utils import Plugin, list_style, print_package_results
from ._pip import _call_pip_install, _call_pip_update, _call_pip_uninstall


def create_plugin(name: Optional[str] = None, plugin_dir: Optional[str] = None):
    if not name:
        question = [{
            "type": "input",
            "name": "plugin_name",
            "message": "Plugin Name:",
            "validate": lambda x: len(x) > 0
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "plugin_name" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        name = answers["plugin_name"]

    if not plugin_dir:
        detected = [
            *filter(lambda x: x.is_dir(),
                    Path(".").glob("**/plugins/")), "Other"
        ]
        question = [{
            "type": "list",
            "name": "plugin_dir",
            "message": "Where to store the plugin?",
            "choices": list(map(str, detected)),
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "plugin_dir" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        plugin_dir = answers["plugin_dir"]
        if plugin_dir == "Other":
            question = [{
                "type": "input",
                "name": "plugin_dir",
                "message": "Plugin Dir:",
                "validate": lambda x: len(x) > 0 and Path(x).is_dir()
            }]
            answers = prompt(question, qmark="[?]", style=list_style)
            if "plugin_dir" not in answers:
                click.secho(f"Error Input!", fg="red")
                return
            plugin_dir = answers["plugin_dir"]
    elif not Path(plugin_dir).is_dir():
        click.secho(f"Plugin Dir is not a directory!", fg="yellow")
        question = [{
            "type": "input",
            "name": "plugin_dir",
            "message": "Plugin Dir:",
            "validate": lambda x: len(x) > 0 and Path(x).is_dir()
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if "plugin_dir" not in answers:
            click.secho(f"Error Input!", fg="red")
            return
        plugin_dir = answers["plugin_dir"]

    question = [{
        "type": "confirm",
        "name": "sub_plugin",
        "message": "Do you want to load sub plugins in current plugin?",
        "default": False
    }]
    answers = prompt(question, qmark="[?]", style=list_style)
    if not answers or "sub_plugin" not in answers:
        click.secho(f"Error Input! Missing 'sub_plugin'", fg="red")
        return
    cookiecutter(str((Path(__file__).parent.parent / "plugin").resolve()),
                 no_input=True,
                 output_dir=plugin_dir,
                 extra_context={
                     "plugin_name": name,
                     "sub_plugin": answers["sub_plugin"]
                 })


def _get_plugin(package: Optional[str], question: str) -> Optional[Plugin]:
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
    plugins = _get_plugins()
    plugin_exact = list(
        filter(
            lambda x: _package == x.id or _package == x.link or _package == x.
            name, plugins))
    if not plugin_exact:
        plugin = list(
            filter(
                lambda x: _package in x.id or _package in x.link or _package in
                x.name, plugins))
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


def search_plugin(package: Optional[str] = None):
    _package: str
    if package is None:
        question = [{
            "type": "input",
            "name": "package",
            "message": "Plugin name you want to search?"
        }]
        answers = prompt(question, qmark="[?]", style=list_style)
        if not answers or "package" not in answers:
            click.secho("Error Input! Missing 'package'", fg="red")
            return
        _package = answers["package"]
    else:
        _package = package
    plugins = _get_plugins()
    plugins = list(
        filter(lambda x: any(_package in value for value in x.dict().values()),
               plugins))
    print_package_results(plugins)


def install_plugin(package: Optional[str] = None,
                   file: str = "pyproject.toml",
                   index: Optional[str] = None):
    plugin = _get_plugin(package, "Plugin name you want to install?")
    if not plugin:
        return
    status = _call_pip_install(plugin.link, index)
    if status == 0:  # SUCCESS
        try:
            if Path(file).suffix == ".toml":
                config = TOMLConfig(file)
            elif Path(file).suffix == ".json":
                config = JSONConfig(file)
            else:
                raise ValueError(
                    "Unknown config file format! Expect 'json' / 'toml'.")
            config.add_plugin(plugin.id)
        except Exception as e:
            click.secho(repr(e), fg="red")


def update_plugin(package: Optional[str] = None, index: Optional[str] = None):
    plugin = _get_plugin(package, "Plugin name you want to update?")
    if not plugin:
        return
    return _call_pip_update(plugin.link, index)


def uninstall_plugin(package: Optional[str] = None,
                     file: str = "pyproject.toml"):
    plugin = _get_plugin(package, "Plugin name you want to uninstall?")
    if not plugin:
        return
    status = _call_pip_uninstall(plugin.link)
    if status == 0:  # SUCCESS
        try:
            if Path(file).suffix == ".toml":
                config = TOMLConfig(file)
            elif Path(file).suffix == ".json":
                config = JSONConfig(file)
            else:
                raise ValueError(
                    "Unknown config file format! Expect 'json' / 'toml'.")
            config.remove_plugin(plugin.id)
        except Exception as e:
            click.secho(repr(e), fg="red")


def _get_plugins() -> List[Plugin]:
    res = httpx.get("https://v2.nonebot.dev/plugins.json")
    plugins = res.json()
    return list(map(lambda x: Plugin(**x), plugins))
