from pathlib import Path
from typing import Any, Dict, List, Optional

import tomlkit
from tomlkit.toml_document import TOMLDocument

from .model import SimpleInfo, NoneBotConfig


class ConfigManager:
    def __init__(
        self,
        python: Optional[str] = None,
        config_file: Path = Path("pyproject.toml"),
        encoding: str = "utf-8",
    ):
        self.python = python
        self.file = config_file
        self.encoding = encoding

    def _get_data(self) -> Optional[TOMLDocument]:
        if self.file.is_file():
            return tomlkit.parse(self.file.read_text(encoding=self.encoding))

    def _write_data(self, data: TOMLDocument) -> None:
        self.file.write_text(tomlkit.dumps(data), encoding=self.encoding)

    def _get_nonebot_config(self, data: TOMLDocument) -> Dict[str, Any]:
        return data.get("tool", {}).get("nonebot", {})

    def get_nonebot_config(self) -> NoneBotConfig:
        return (
            NoneBotConfig.parse_obj(self._get_nonebot_config(data))
            if (data := self._get_data())
            else NoneBotConfig()
        )

    def add_adapter(self, adapter: SimpleInfo) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        adapters: List[Dict[str, Any]] = table.setdefault("adapters", [])
        if all(a["module_name"] != adapter.module_name for a in adapters):
            t = tomlkit.inline_table()
            t.update(adapter.dict())
            adapters.append(t)
        self._write_data(data)

    def remove_adapter(self, adapter: SimpleInfo) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        adapters: List[Dict[str, Any]] = table.setdefault("adapters", [])
        if index := next(
            (
                i
                for i, a in enumerate(adapters)
                if a["module_name"] == adapter.module_name
            ),
            None,
        ):
            del adapters[index]
        self._write_data(data)

    def add_plugin(self, plugin: str) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_plugin(self, plugin: str) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)

    def add_builtin_plugin(self, plugin: str) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("builtin_plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_builtin_plugin(self, plugin: str) -> None:
        if not (data := self._get_data()):
            raise RuntimeError("Config file not found!")
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("builtin_plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)
