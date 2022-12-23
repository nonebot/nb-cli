from pathlib import Path
from typing import Any, Dict

import tomlkit
from tomlkit.items import SingleKey
from tomlkit.toml_document import TOMLDocument

from .model import Config


class ConfigManager:
    def __init__(self, config_file: Path, encoding: str = "utf-8"):
        if not config_file.is_file():
            raise RuntimeError(f"Config file {config_file} does not exist!")
        self.file = config_file
        self.encoding = encoding

    def _get_data(self) -> TOMLDocument:
        return tomlkit.parse(self.file.read_text(encoding=self.encoding))

    def _write_data(self, data: TOMLDocument) -> None:
        self.file.write_text(tomlkit.dumps(data), encoding=self.encoding)

    def _get_cli_config(self, data: TOMLDocument) -> Dict[str, Any]:
        return data.get(SingleKey("tool").concat(SingleKey("nb_cli")), {})

    def _get_bot_config(self, data: TOMLDocument) -> Dict[str, Any]:
        return data.get(SingleKey("tool").concat(SingleKey("nonebot")), {})

    def _get_config(self, data: TOMLDocument) -> Dict[str, Dict[str, Any]]:
        return {
            "nb_cli": self._get_cli_config(data),
            "nonebot": self._get_bot_config(data),
        }

    def get_config(self) -> Config:
        return Config.parse_obj(self._get_config(self._get_data()))
