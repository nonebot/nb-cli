"""本模块定义插件加载接口。

FrontMatter:
    sidebar_position: 1
    description: nb_cli.plugin.load 模块
"""
from pathlib import Path
from types import ModuleType
from typing import Set, Union, Iterable, Optional

import tomlkit

from .plugin import Plugin
from .manager import PluginManager
from .utils import path_to_module_name
from . import _managers, get_plugin, _module_name_to_plugin_name


def load_plugin(module_path: Union[str, Path]) -> Optional[Plugin]:
    """加载单个插件，可以是本地插件或是通过 `pip` 安装的插件。

    参数:
        module_path: 插件名称 `path.to.your.plugin` 或插件路径 `pathlib.Path(path/to/your/plugin)`
    """
    module_path = (
        path_to_module_name(module_path)
        if isinstance(module_path, Path)
        else module_path
    )
    manager = PluginManager([module_path])
    _managers.append(manager)
    return manager.load_plugin(module_path)


def load_plugins(*plugin_dir: str) -> Set[Plugin]:
    """导入文件夹下多个插件，以 `_` 开头的插件不会被导入!

    参数:
        plugin_dir: 文件夹路径
    """
    manager = PluginManager(search_path=plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_all_plugins(
    module_path: Iterable[str], plugin_dir: Iterable[str]
) -> Set[Plugin]:
    """导入指定列表中的插件以及指定目录下多个插件，以 `_` 开头的插件不会被导入!

    参数:
        module_path: 指定插件集合
        plugin_dir: 指定文件夹路径集合
    """
    manager = PluginManager(module_path, plugin_dir)
    _managers.append(manager)
    return manager.load_all_plugins()


def load_from_toml(file_path: str, encoding: str = "utf-8") -> Set[Plugin]:
    """导入指定 toml 文件 `[tool.nonebot]` 中的 `cli_plugins` 以及 `cli_plugin_dirs` 下多个插件，以 `_` 开头的插件不会被导入!

    参数:
        file_path: 指定 toml 文件路径
        encoding: 指定 toml 文件编码

    用法:
        ```toml title=pyproject.toml
        [tool.nonebot]
        cli_plugins = ["some_plugin"]
        cli_plugin_dirs = ["some_dir"]
        ```
    """
    with open(file_path, "r", encoding=encoding) as f:
        data = tomlkit.parse(f.read())  # type: ignore

    nb_cli_data = data.get("tool", {}).get("nonebot")
    if nb_cli_data is None:
        raise ValueError("Cannot find '[tool.nonebot]' in given toml file!")
    if not isinstance(nb_cli_data, dict):
        raise TypeError("'[tool.nonebot]' must be a Table!")
    cli_plugins = nb_cli_data.get("cli_plugins", [])
    cli_plugin_dirs = nb_cli_data.get("cli_plugin_dirs", [])
    assert isinstance(
        cli_plugins, list
    ), "plugins must be a list of plugin name"
    assert isinstance(
        cli_plugin_dirs, list
    ), "plugin_dirs must be a list of directories"
    return load_all_plugins(cli_plugins, cli_plugin_dirs)


def _find_manager_by_name(name: str) -> Optional[PluginManager]:
    for manager in reversed(_managers):
        if name in manager.plugins or name in manager.searched_plugins:
            return manager


def require(name: str) -> ModuleType:
    """获取一个插件的导出内容。

    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。

    参数:
        name: 插件名，即 {ref}`nb_cli.plugin.plugin.Plugin.name`。

    异常:
        RuntimeError: 插件无法加载
    """
    plugin = get_plugin(_module_name_to_plugin_name(name))
    if not plugin:
        if manager := _find_manager_by_name(name):
            plugin = manager.load_plugin(name)
        else:
            plugin = load_plugin(name)
    if not plugin:
        raise RuntimeError(f'Cannot load plugin "{name}"!')
    return plugin.module
