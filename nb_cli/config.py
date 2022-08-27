from pathlib import Path
from typing import Set, List

import tomlkit
from pydantic import BaseSettings

from nb_cli.utils import DATA_DIR
from nb_cli.handlers._config import JSONConfig, TOMLConfig


class Config(BaseSettings):
    reload: bool = False
    reload_dirs: List[Path] = []
    reload_dirs_excludes: List[Path] = []
    reload_excludes: Set[str] = set()
    reload_includes: Set[str] = set()

    class Config:
        extra = "allow"
        env_prefix = "nb_cli_"


class ConfigManager:
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

    @classmethod
    def get_global_config(cls):
        path = Path(DATA_DIR) / "config.toml"
        if not path.exists():
            with open(path, "w") as f:
                return Config()
        else:
            with open(path, "r") as f:
                data = tomlkit.parse(f.read())
                return Config(**data)
