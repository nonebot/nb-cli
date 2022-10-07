"""本模块为 NoneBot CLI 插件开发提供便携的定义函数。
## 快捷导入
为方便使用，本模块从子模块导入了部分内容，以下内容可以直接通过本模块导入:
- `load_plugin` => {ref}``load_plugin` <nb_cli.plugin.load.load_plugin>`
- `load_plugins` => {ref}``load_plugins` <nb_cli.plugin.load.load_plugins>`
- `load_all_plugins` => {ref}``load_all_plugins` <nb_cli.plugin.load.load_all_plugins>`
- `load_from_toml` => {ref}``load_from_toml` <nb_cli.plugin.load.load_from_toml>`
- `require` => {ref}``require` <nb_cli.plugin.load.require>`
- `PluginMetadata` => {ref}``PluginMetadata` <nb_cli.plugin.plugin.PluginMetadata>`
FrontMatter:
    sidebar_position: 0
    description: nb_cli.plugin 模块
"""

from itertools import chain
from types import ModuleType
from contextvars import ContextVar
from typing import Set, Dict, List, Tuple, Optional

_plugins: Dict[str, "Plugin"] = {}
_managers: List["PluginManager"] = []
_current_plugin_chain: ContextVar[Tuple["Plugin", ...]] = ContextVar(
    "_current_plugin_chain", default=tuple()
)


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit(".", 1)[-1]


def _new_plugin(
    module_name: str, module: ModuleType, manager: "PluginManager"
) -> "Plugin":
    plugin_name = _module_name_to_plugin_name(module_name)
    if plugin_name in _plugins:
        raise RuntimeError("Plugin already exists! Check your plugin name.")
    plugin = Plugin(plugin_name, module, module_name, manager)
    _plugins[plugin_name] = plugin
    return plugin


def _revert_plugin(plugin: "Plugin") -> None:
    if plugin.name not in _plugins:
        raise RuntimeError("Plugin not found!")
    del _plugins[plugin.name]


def get_plugin(name: str) -> Optional["Plugin"]:
    """获取已经导入的某个插件。
    如果为 `load_plugins` 文件夹导入的插件，则为文件(夹)名。
    参数:
        name: 插件名，即 {ref}`nb_cli.plugin.Plugin.name`。
    """
    return _plugins.get(name)


def get_plugin_by_module_name(module_name: str) -> Optional["Plugin"]:
    """通过模块名获取已经导入的某个插件。
    如果提供的模块名为某个插件的子模块，同样会返回该插件。
    参数:
        module_name: 模块名，即 {ref}`nb_cli.plugin.Plugin.module_name`。
    """
    loaded = {plugin.module_name: plugin for plugin in _plugins.values()}
    has_parent = True
    while has_parent:
        if module_name in loaded:
            return loaded[module_name]
        module_name, *has_parent = module_name.rsplit(".", 1)


def get_loaded_plugins() -> Set["Plugin"]:
    """获取当前已导入的所有插件。"""
    return set(_plugins.values())


def get_available_plugin_names() -> Set[str]:
    """获取当前所有可用的插件名（包含尚未加载的插件）。"""
    return {
        *chain.from_iterable(manager.available_plugins for manager in _managers)
    }


from .manager import PluginManager
from .load import require as require
from .plugin import Plugin as Plugin
from .load import load_plugin as load_plugin
from .load import load_plugins as load_plugins
from .load import load_from_toml as load_from_toml
from .plugin import PluginMetadata as PluginMetadata
from .load import load_all_plugins as load_all_plugins
