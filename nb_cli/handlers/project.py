from pathlib import Path

import click
from PyInquirer import prompt
from cookiecutter.main import cookiecutter

from .adapter import _get_adapters
from ._pip import _call_pip_install
from nb_cli.utils import list_style


def create_project():
    click.secho("Loading adapters...")
    adapters = {x.name: x for x in _get_adapters()}
    click.clear()
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
        "choices": [{
            "name": name
        } for name in adapters.keys()]
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
    answers["adapters"] = {
        "builtin": [adapters[name].dict() for name in answers2["adapters"]]
    }
    cookiecutter(str((Path(__file__).parent.parent / "project").resolve()),
                 no_input=True,
                 extra_context=answers)

    for adapter in answers["adapters"]["builtin"]:
        _call_pip_install(adapter["link"])
