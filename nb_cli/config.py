import abc
import json
from typing import Any
from pathlib import Path

import tomlkit
from tomlkit.items import Array, Table
from tomlkit.toml_document import TOMLDocument

from nb_cli.utils import DATA_DIR
from nb_cli.consts import ARRAY_CONFIGS


class LocalConfig(abc.ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def append(self, key: str, value: Any):
        raise NotImplementedError

    @abc.abstractmethod
    def remove(self, key: str, value: Any):
        raise NotImplementedError

    @abc.abstractmethod
    def print(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, key: str, value: Any):
        raise NotImplementedError

    @abc.abstractmethod
    def unset(self, key: str):
        raise NotImplementedError

    def add_plugin(self, plugin_name: str):
        self.append("plugins", plugin_name)

    def remove_plugin(self, plugin_name: str):
        self.remove("plugins", plugin_name)

    def add_plugin_dir(self, dir_name: str):
        self.append("plugin_dirs", dir_name)

    def remove_plugin_dir(self, dir_name: str):
        self.remove("plugin_dirs", dir_name)

    def get_adapters(self):
        return self.get("adapters")

    def get_builtin_plugins(self):
        return self.get("builtin_plugins")

    def add_adapter(self, adapter_name: str):
        self.append("adapters", adapter_name)

    def add_builtin_plugin(self, plugin_name: str):
        self.append("builtin_plugins", plugin_name)

    def remove_adapter(self, adapter_name: str):
        self.remove("adapters", adapter_name)

    def remove_builtin_plugin(self, plugin_name: str):
        self.remove("builtin_plugins", plugin_name)


class TOMLConfig(LocalConfig):
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

    def _validate_table(self, data, key):
        updated_data = data.setdefault(key, tomlkit.table())
        if not isinstance(updated_data, Table):
            raise ValueError(f"'{key}' in toml file is not a Table!")
        return updated_data

    def _validate_array(self, data, key):
        updated_data = data.setdefault(key, tomlkit.array())
        if not isinstance(updated_data, Array):
            raise ValueError(f"'{key}' in toml file is not a Array!")
        return updated_data

    def _validate_bool(self, data, key, default):
        updated_data = data.setdefault(key, tomlkit.boolean(default))
        if not isinstance(updated_data, bool):
            raise ValueError(f"'{key}' in toml file is not a Boolean!")
        return updated_data

    def _validate(self, data: TOMLDocument) -> None:
        tool_data = self._validate_table(data, "tool")
        nonebot_data = self._validate_table(tool_data, "tool")

        for key in ARRAY_CONFIGS:
            self._validate_array(nonebot_data, key)

        self._validate_bool(nonebot_data, "reload", "false")

    def append(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        sub_data: Array = data["tool"]["nonebot"][key]  # type: ignore
        if value not in sub_data:
            sub_data.append(value)
        self._write_data(data)

    def remove(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        sub_data: Array = data["tool"]["nonebot"][key]  # type: ignore
        del sub_data[sub_data.index(value)]
        self._write_data(data)

    def print(self):
        data = self._get_data()
        self._validate(data)
        print(data["tool"]["nonebot"])  # type: ignore

    def get(self, key: str):
        data = self._get_data()
        self._validate(data)
        value = data["tool"]["nonebot"].get(key)  # type: ignore
        return value

    def update(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        data["tool"]["nonebot"][key] = value  # type: ignore
        self._write_data(data)

    def unset(self, key: str):
        data = self._get_data()
        self._validate(data)
        del data["tool"]["nonebot"][key]  # type: ignore
        self._write_data(data)


class JSONConfig(LocalConfig):
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

    def append(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        sub_data: Array = data[key]
        if value not in sub_data:
            sub_data.append(value)
        self._write_data(data)

    def remove(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        sub_data: Array = data[key]
        del sub_data[sub_data.index(value)]
        self._write_data(data)

    def print(self):
        data = self._get_data()
        self._validate(data)
        print(data)

    def get(self, key: str):
        data = self._get_data()
        self._validate(data)
        value = data.get(key)
        return value

    def update(self, key: str, value: Any):
        data = self._get_data()
        self._validate(data)
        data[key] = value
        self._write_data(data)

    def unset(self, key: str):
        data = self._get_data()
        self._validate(data)
        del data[key]
        self._write_data(data)


"""
class Config(BaseSettings):
    reload: bool = False
    reload_dirs: List[Path] = []
    reload_dirs_excludes: List[Path] = []
    reload_excludes: Set[str] = set()
    reload_includes: Set[str] = set()

    class Config:
        extra = "allow"
        env_prefix = "nb_cli_"
"""


class ConfigManager:
    GLOBAL_CONFIG_PATH = (Path(DATA_DIR) / "config.toml").resolve()

    @classmethod
    def get_local_config(cls, file: str):
        if Path(file).suffix == ".toml":
            local_config = TOMLConfig(file)
        elif Path(file).suffix == ".json":
            local_config = JSONConfig(file)
        else:
            raise ValueError(
                "Unknown config file format! Expect 'json' / 'toml'."
            )

        return local_config


"""
    @classmethod
    def get_global_config(cls):
        if not cls.GLOBAL_CONFIG_PATH.exists():
            with open(cls.GLOBAL_CONFIG_PATH, "w") as f:
                return Config()
        else:
            with open(cls.GLOBAL_CONFIG_PATH, "r") as f:
                data = tomlkit.parse(f.read())
                return Config(**data)

    @classmethod
    def set_global_config(cls, config):
        with open(cls.GLOBAL_CONFIG_PATH, "w") as f:
            f.write(tomlkit.dumps(config.dict()))
"""
