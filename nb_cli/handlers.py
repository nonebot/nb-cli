import os
import sys
import logging
import importlib
from pathlib import Path
from functools import partial
from typing import List, Iterable, Optional

try:
    from pip._internal.cli.main import main as pipmain
except ImportError:
    from pip import main as pipmain

import click
import httpx
import nonebot
import nonebot.adapters
from PyInquirer import prompt
from pyfiglet import figlet_format
from cookiecutter.main import cookiecutter

try:
    from compose.cli.main import TopLevelCommand, DocoptDispatcher, AnsiMode
    from compose.cli.main import setup_console_handler, setup_parallel_logger, perform_command
    COMPOSE_INSTALLED = True
except ImportError:
    COMPOSE_INSTALLED = False

from nb_cli.utils import Plugin, Adapter, list_style, print_package_results


def draw_logo():
    click.secho(figlet_format("NoneBot", font="basic").strip(),
                fg="cyan",
                bold=True)


def run_bot(file: str = "bot.py", app: str = "app"):
    if not os.path.isfile(file):
        click.secho(f"Cannot find {file} in current folder!", fg="red")
        return

    module_name, _ = os.path.splitext(file)
    module = importlib.import_module(module_name)
    _app = getattr(module, app)
    if not _app:
        click.secho(
            "Cannot find an asgi server. Add `app = nonebot.get_asgi()` to enable reload mode."
        )
        nonebot.run()
    else:
        nonebot.run(app=f"{module_name}:{app}")


def create_project():
    adapters = [{
        "name": x.name
    }
                for x in Path(nonebot.adapters.__path__[0]).iterdir()
                if x.is_dir() and not x.name.startswith("_")]
    question = [{
        "type": "input",
        "name": "project_name",
        "message": "Project Name:",
        "validate": lambda x: len(x) > 0
    }, {
        "type":
            "list",
        "name":
            "use_src",
        "message":
            "Where to store the plugin?",
        "choices":
            lambda ctx: [
                f"1) In a \"{ctx['project_name'].lower().replace(' ', '-').replace('-', '_')}\" folder",
                "2) In a \"src\" folder"
            ],
        "filter":
            lambda x: x.startswith("2")
    }, {
        "type": "confirm",
        "name": "load_builtin",
        "message": "Load NoneBot Builtin Plugin?",
        "default": False
    }]
    keys = set(map(lambda x: x["name"], question))
    answers = prompt(question, qmark="[?]", style=list_style)
    if keys != set(answers.keys()):
        click.secho(f"Error Input! Missing {list(keys - set(answers.keys()))}",
                    fg="red")
        return
    question2 = [{
        "type": "checkbox",
        "name": "adapters",
        "message": "Which adapter(s) would you like to use?",
        "choices": adapters
    }, {
        "type": "confirm",
        "name": "confirm",
        "message": "You haven't chosen any adapter. Please confirm.",
        "default": False,
        "when": lambda x: not bool(x["adapters"])
    }]
    while True:
        answers2 = prompt(question2, qmark="[?]", style=list_style)
        if "adapters" not in answers2:
            click.secho(f"Error Input! Missing 'adapters'", fg="red")
            return
        if answers2["adapters"] or answers2["confirm"]:
            break
    answers["adapters"] = {"builtin": answers2["adapters"]}
    cookiecutter(str((Path(__file__).parent / "project").resolve()),
                 no_input=True,
                 extra_context=answers)


def handle_no_subcommand():
    draw_logo()
    click.echo("\n\b")
    click.secho("Welcome to NoneBot CLI!", fg="green", bold=True)

    choices = {
        "Show Logo":
            draw_logo,
        "Create a New Project":
            create_project,
        "Run the Bot in Current Folder":
            run_bot,
        "Build Docker Image for the Bot":
            partial(_call_docker_compose, "build", []),
        "Deploy the Bot to Docker":
            partial(_call_docker_compose, "up", ["-d"]),
        "Stop the Bot Container in Docker":
            partial(_call_docker_compose, "down"),
        "Create a New NoneBot Plugin":
            create_plugin,
        "List All Published Plugins":
            partial(search_plugin, ""),
        "Search for Published Plugin":
            search_plugin,
        "Install a Published Plugin":
            install_plugin,
        "Update a Published Plugin":
            update_plugin,
    }
    question = [{
        "type": "list",
        "name": "subcommand",
        "message": "What do you want to do?",
        "choices": choices.keys(),
        "filter": lambda x: choices[x]
    }]
    answers = prompt(question, style=list_style)
    if "subcommand" not in answers or not answers["subcommand"]:
        click.secho("Error Input!", fg="red")
        return
    answers["subcommand"]()


def _call_docker_compose(command: str, args: Iterable[str]):
    if not COMPOSE_INSTALLED:
        click.secho(
            "docker-compose not found! install it by using `pip install nb-cli[deploy]`",
            fg="red")
        return
    console_stream = sys.stderr
    console_handler = logging.StreamHandler(console_stream)
    dispatcher = DocoptDispatcher(TopLevelCommand, {"options_first": True})
    options, handler, command_options = dispatcher.parse([command, *args])
    ansi_mode = AnsiMode.AUTO
    setup_console_handler(logging.StreamHandler(sys.stderr),
                          options.get('--verbose'),
                          ansi_mode.use_ansi_codes(console_handler.stream),
                          options.get("--log-level"))
    setup_parallel_logger(ansi_mode)
    if ansi_mode is AnsiMode.NEVER:
        command_options['--no-color'] = True
    return perform_command(options, handler, command_options)


def create_adapter(name: Optional[str] = None,
                   adapter_dir: Optional[str] = None):
    pass


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
    cookiecutter(str((Path(__file__).parent / "plugin").resolve()),
                 no_input=True,
                 output_dir=plugin_dir,
                 extra_context={
                     "plugin_name": name,
                     "sub_plugin": answers["sub_plugin"]
                 })


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
                   file: str = "bot.py",
                   index: Optional[str] = None):
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
    plugin_exact = list(
        filter(lambda x: _package == x.id or _package == x.name, plugins))
    if not plugin_exact:
        plugin = list(
            filter(lambda x: _package in x.id or _package in x.name, plugins))
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
    status = _call_pip_install(plugin.link, index)
    if status == 0 and os.path.isfile(file):  # SUCCESS
        with open(file, "r") as f:
            lines = f.readlines()
        insert_index = len(lines) - list(
            map(
                lambda x: x.startswith("nonebot.load") or x.startswith(
                    "nonebot.init"), lines[::-1])).index(True)
        lines.insert(insert_index, f"nonebot.load_plugin(\"{plugin.id}\")\n")
        with open(file, "w") as f:
            f.writelines(lines)
    elif status == 0:
        click.secho(f"Cannot find {file} in current folder!", fg="red")


def update_plugin(package: Optional[str] = None, index: Optional[str] = None):
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
    plugin_exact = list(
        filter(lambda x: _package == x.id or _package == x.name, plugins))
    if not plugin_exact:
        plugin = list(
            filter(lambda x: _package in x.id or _package in x.name, plugins))
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
    return _call_pip_update(plugin.link, index)


def _get_adapters() -> List[Adapter]:
    res = httpx.get("https://v2.nonebot.dev/adapters.json")
    adapters = res.json()
    return list(map(lambda x: Adapter(**x), adapters))


def _get_plugins() -> List[Plugin]:
    res = httpx.get("https://v2.nonebot.dev/plugins.json")
    plugins = res.json()
    return list(map(lambda x: Plugin(**x), plugins))


def _call_pip_install(package: str, index: Optional[str] = None):
    if index:
        return pipmain(["install", "-i", index, package])
    else:
        return pipmain(["install", package])


def _call_pip_update(package: str, index: Optional[str] = None):
    if index:
        return pipmain(["install", "--upgrade", "-i", index, package])
    else:
        return pipmain(["install", "--upgrade", package])
