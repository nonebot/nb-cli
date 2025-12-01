import json
import asyncio
from pathlib import Path

from cookiecutter.main import cookiecutter

from nb_cli.compat import model_dump
from nb_cli.exceptions import ProjectInvalidError
from nb_cli.config import Plugin, NoneBotConfig, LegacyNoneBotConfig

from . import templates
from .process import create_process
from .store import load_module_data, load_unpublished_modules
from .meta import (
    requires_nonebot,
    get_default_python,
    get_nonebot_config,
    requires_project_root,
)

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "plugin"


@requires_nonebot
async def list_builtin_plugins(*, python_path: str | None = None) -> list[str]:
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
    template: str | None = None,
):
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=True,
        output_dir=output_dir,
        extra_context={"plugin_name": plugin_name, "sub_plugin": sub_plugin},
    )


async def list_plugins(
    query: str | None = None, include_unpublished: bool = False
) -> list[Plugin]:
    plugins = await load_module_data("plugin")
    if include_unpublished:
        plugins = plugins + await load_unpublished_modules(Plugin)
    if query is None:
        return plugins

    return [
        plugin
        for plugin in plugins
        if any(
            query in value
            for value in model_dump(
                plugin, include={"name", "module_name", "project_link", "desc"}
            ).values()
        )
    ]


@requires_project_root
async def list_installed_plugins(*, cwd: Path | None = None) -> list[Plugin]:
    config_data = get_nonebot_config(cwd)
    plugins = await load_module_data("plugin") + await load_unpublished_modules(Plugin)

    result: list[Plugin] = []

    if isinstance(config_data, NoneBotConfig):
        plugin_info = config_data.plugins
        allowed_plugins = {
            (pkg_name, module_name)
            for pkg_name, module_names in plugin_info.items()
            for module_name in module_names
        }
        for plugin in plugins:
            if (plugin.project_link, plugin.module_name) in allowed_plugins:
                result.append(plugin)
    elif isinstance(config_data, LegacyNoneBotConfig):
        plugin_info = config_data.plugins
        allowed_plugins = set(plugin_info)
        for plugin in plugins:
            if plugin.module_name in allowed_plugins:
                result.append(plugin)
    else:
        raise ProjectInvalidError("Invalid config data type")

    return result
