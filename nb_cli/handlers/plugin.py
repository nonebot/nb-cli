import json
import asyncio
from pathlib import Path
from typing import List, Optional

from cookiecutter.main import cookiecutter

from . import templates
from .config import ConfigManager
from .meta import requires_nonebot
from .process import create_process
from .store import Plugin, load_module_data

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "plugin"


@requires_nonebot
async def list_builtin_plugins(
    *, config_manager: Optional[ConfigManager] = None
) -> List[str]:
    python_path = await (config_manager or ConfigManager()).get_python_path()

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
