import os
import abc
import json

import tomlkit
from tomlkit.items import Table, Array
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


class TOMLConfig(Config):

    def __init__(self, file: str):
        if not os.path.isfile(file):
            raise RuntimeError(f"Config file {file} does not exist!")
        self.file = file

    def _get_data(self) -> TOMLDocument:
        with open(self.file, "r", encoding="utf-8") as f:
            return tomlkit.parse(f.read())

    def _write_data(self, data: TOMLDocument) -> None:
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(data))

    def _validate(self, data: TOMLDocument) -> None:
        nonebot_data = data.setdefault("nonebot", tomlkit.table())
        if not isinstance(nonebot_data, Table):
            raise ValueError("'nonebot' in toml file is not a Table!")
        plugin_data = nonebot_data.setdefault("plugins", tomlkit.table())
        if not isinstance(plugin_data, Table):
            raise ValueError("'nonebot.plugins' in toml file is not a Table!")
        plugins = plugin_data.setdefault("plugins", tomlkit.array())
        if not isinstance(plugins, Array):
            raise ValueError(
                "'nonebot.plugins.plugins' in toml file is not a Array!")
        plugin_dirs = plugin_data.setdefault("plugin_dirs", tomlkit.array())
        if not isinstance(plugin_dirs, Array):
            raise ValueError(
                "'nonebot.plugins.plugin_dirs' in toml file is not a Array!")

    def add_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: Array = data["nonebot"]["plugins"]["plugins"]  # type: ignore
        if plugin_name not in plugins:
            plugins.append(plugin_name)
        self._write_data(data)

    def remove_plugin(self, plugin_name: str):
        data = self._get_data()
        self._validate(data)
        plugins: Array = data["nonebot"]["plugins"]["plugins"]  # type: ignore
        del plugins[plugins.index(plugin_name)]
        self._write_data(data)

    def add_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: Array = data["nonebot"]["plugins"][  # type: ignore
            "plugin_dirs"]
        if dir_name not in plugin_dirs:
            plugin_dirs.append(dir_name)
        self._write_data(data)

    def remove_plugin_dir(self, dir_name: str):
        data = self._get_data()
        self._validate(data)
        plugin_dirs: Array = data["nonebot"]["plugins"][  # type: ignore
            "plugin_dirs"]
        plugin_dirs.remove(dir_name)
        self._write_data(data)


class JSONConfig(Config):

    def __init__(self, file: str):
        if not os.path.isfile(file):
            raise RuntimeError(f"Config file {file} does not exist!")
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
