import sys
import json
import subprocess
from pathlib import Path
from typing import List, Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import Plugin

from . import templates
from .meta import get_config, requires_pip, load_module_data, requires_nonebot

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "plugin"


@requires_nonebot
def list_builtin_plugins(python_path: Optional[str] = None) -> List[str]:
    if python_path is None:
        python_path = get_config().nb_cli.python

    t = templates.get_template("plugin/list_builtin_plugin.py.jinja")

    output = subprocess.check_output(
        [python_path, "-W", "ignore", "-c", t.render()], text=True
    )
    return json.loads(output)


def create_plugin(
    plugin_name: str,
    output_dir: str = ".",
    sub_plugin: bool = False,
    template: Optional[str] = None,
):
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=True,
        output_dir=output_dir,
        extra_context={"plugin_name": plugin_name, "sub_plugin": sub_plugin},
    )


def list_plugins(query: Optional[str] = None) -> List[Plugin]:
    plugins = load_module_data("plugin")
    if query is None:
        return plugins

    return [
        plugin
        for plugin in plugins
        if any(query in value for value in plugin.dict().values())
    ]
