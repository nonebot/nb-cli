import json
import asyncio
from pathlib import Path
from typing import List, Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import Plugin

from . import templates
from .process import create_process
from .store import load_module_data
from .meta import requires_nonebot, get_default_python

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "plugin"


@requires_nonebot
async def list_builtin_plugins(*, python_path: Optional[str] = None) -> List[str]:
    if python_path is None:
        python_path = await get_default_python()

    t = templates.get_template("plugin/list_builtin_plugin.py.jinja")

    proc = await create_process(
        python_path,
        "-W",
        "ignore",
        "-c",
        await t.render_async(),
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return json.loads(stdout.strip())


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


async def list_plugins(query: Optional[str] = None) -> List[Plugin]:
    plugins = await load_module_data("plugin")
    if query is None:
        return plugins

    return [
        plugin
        for plugin in plugins
        if any(query in value for value in plugin.dict().values())
    ]
