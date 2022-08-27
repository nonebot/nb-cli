import abc
import json
from pathlib import Path

import tomlkit
from tomlkit.items import Array, Table
from tomlkit.toml_document import TOMLDocument


class Config(abc.ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def add_plugin(self, plugin_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_plugin(self, plugin_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def add_plugin_dir(self, dir_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_plugin_dir(self, dir_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def get_adapters(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_builtin_plugins(self):
        raise NotImplementedError

    @abc.abstractmethod
    def add_adapter(self, adapter_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def add_builtin_plugin(self, plugin_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_adapter(self, adapter_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_builtin_plugin(self, plugin_name: str):
        raise NotImplementedError


class TOMLConfig(Config):
    def __init__(self, file: str):
        path = Path(file).resolve()
        if not path.is_file():
            raise RuntimeError(f"Config file {path} does not exist!")
        self.file = file

    def _get_data(self) -> TOMLDocument:
        with open(self.file, "r", encoding="utf-8") as f:
            return tomlkit.parse(f.read())

    def _write_data(self, data: TOMLDocument) -> None:
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(data))

    def _validate(self, data: TOMLDocument) -> None:
        tool_data = data.setdefault("tool", tomlkit.table())
        if not isinstance(tool_data, Table):
            raise ValueError("'tool' in toml file is not a Table!")
        nonebot_data = tool_data.setdefault("nonebot", tomlkit.table())
        if not isinstance(nonebot_data, Table):
            raise ValueError("'tool.nonebot' in toml file is not a Table!")
        plugins = nonebot_data.setdefault("plugins", tomlkit.array())
        if not isinstance(plugins, Array):
            raise ValueError(
                "'tool.nonebot.plugins' in toml file is not a Array!"
            )
        plugin_dirs = nonebot_data.setdefault("plugin_dirs", tomlkit.array())
        if not isinstance(plugin_dirs, Array):
            raise ValueError(
                "'tool.nonebot.plugin_dirs' in toml file is not a Array!"
            )

    def add_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: Array = data["tool"]["nonebot"]["plugins"]  # type: ignore
        if plugin_name not in plugins:
            plugins.append(plugin_name)
        self._write_data(data)

    def remove_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: Array = data["tool"]["nonebot"]["plugins"]  # type: ignore
        del plugins[plugins.index(plugin_name)]
        self._write_data(data)

    def add_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: Array = data["tool"]["nonebot"][  # type: ignore
            "plugin_dirs"
        ]
        if dir_name not in plugin_dirs:
            plugin_dirs.append(dir_name)
        self._write_data(data)

    def remove_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: Array = data["tool"]["nonebot"][  # type: ignore
            "plugin_dirs"
        ]
        plugin_dirs.remove(dir_name)
        self._write_data(data)

    def get_adapters(self):
        data = self._get_data()
        self._validate(data)
        adapters: Array = data["tool"]["nonebot"]["adapters"]  # type: ignore
        return adapters

    def get_builtin_plugins(self):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: Array = data["tool"]["nonebot"]["builtin_plugins"]  # type: ignore
        return builtin_plugins

    def add_adapter(self, adapter_name: str):
        data = self._get_data()
        self._validate(data)
        adapters: Array = data["tool"]["nonebot"]["adapters"]  # type: ignore
        if adapter_name not in adapters:
            adapters.append(adapter_name)
        self._write_data(data)

    def add_builtin_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: Array = data["tool"]["nonebot"]["builtin_plugins"]  # type: ignore
        if plugin_name not in builtin_plugins:
            builtin_plugins.append(plugin_name)
        self._write_data(data)

    def remove_adapter(self, adapter_name: str):
        data = self._get_data()
        self._validate(data)
        adapters: Array = data["tool"]["nonebot"]["adapters"]  # type: ignore
        adapters.remove(adapter_name)
        self._write_data(data)

    def remove_builtin_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: Array = data["tool"]["nonebot"]["builtin_plugins"]  # type: ignore
        builtin_plugins.remove(plugin_name)
        self._write_data(data)


class JSONConfig(Config):
    def __init__(self, file: str):
        path = Path(file).resolve()
        if not path.is_file():
            raise RuntimeError(f"Config file {path} does not exist!")
        self.file = file

    def _get_data(self):
        with open(self.file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_data(self, data):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _validate(self, data):
        if not isinstance(data, dict):
            raise ValueError("Data in file is not a dict!")
        plugins = data.setdefault("plugins", [])
        if not isinstance(plugins, list):
            raise ValueError("'plugins' is not a list!")
        plugin_dirs = data.setdefault("plugin_dirs", [])
        if not isinstance(plugin_dirs, list):
            raise ValueError("'plugin_dirs' is not a list!")

    def add_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: list = data["plugins"]
        if plugin_name not in plugins:
            plugins.append(plugin_name)
        self._write_data(data)

    def remove_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: list = data["plugins"]
        plugins.remove(plugin_name)
        self._write_data(data)

    def add_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: list = data["plugin_dirs"]
        if dir_name not in plugin_dirs:
            plugin_dirs.append(dir_name)
        self._write_data(data)

    def remove_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: list = data["plugin_dir"]
        plugin_dirs.remove(dir_name)
        self._write_data(data)

    def get_adapters(self):
        data = self._get_data()
        self._validate(data)
        adapters: list = data["adapters"]
        return adapters

    def get_builtin_plugins(self):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: list = data["builtin_plugins"]
        return builtin_plugins

    def add_adapter(self, adapter_name: str):
        data = self._get_data()
        self._validate(data)
        adapters: list = data["adapters"]
        if adapter_name not in adapters:
            adapters.append(adapter_name)
        self._write_data(data)

    def add_builtin_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: list = data["builtin_plugins"]
        if plugin_name not in builtin_plugins:
            builtin_plugins.append(plugin_name)
        self._write_data(data)

    def remove_adapter(self, adapter_name: str):
        data = self._get_data()
        self._validate(data)
        adapters: list = data["adapters"]
        adapters.remove(adapter_name)
        self._write_data(data)

    def remove_builtin_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        builtin_plugins: list = data["builtin_plugins"]
        builtin_plugins.remove(plugin_name)
        self._write_data(data)
