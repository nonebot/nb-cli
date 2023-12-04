import logging
from pathlib import Path
from typing import Any, Dict, List, ClassVar, Optional

import tomlkit
from tomlkit.toml_document import TOMLDocument

from nb_cli import _
from nb_cli.log import SUCCESS
from nb_cli.consts import WINDOWS
from nb_cli.exceptions import ProjectNotFoundError

from .model import SimpleInfo, NoneBotConfig

CONFIG_FILE = "pyproject.toml"
CONFIG_FILE_ENCODING = "utf-8"


class ConfigManager:
    _global_working_dir: ClassVar[Optional[Path]] = None
    _global_python_path: ClassVar[Optional[str]] = None
    _global_use_venv: ClassVar[bool] = True
    _path_venv_cache: ClassVar[Dict[Path, Optional[str]]] = {}

    def __init__(
        self,
        *,
        working_dir: Optional[Path] = None,
        python_path: Optional[str] = None,
        use_venv: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._working_dir = working_dir
        self._python_path = python_path
        self._use_venv = use_venv
        self._logger = logger

    @property
    def working_dir(self) -> Path:
        return (self._working_dir or self._global_working_dir or Path.cwd()).resolve()

    @staticmethod
    def _locate_project_root(cwd: Optional[Path] = None) -> Path:
        cwd = (cwd or Path.cwd()).resolve()
        for dir in (cwd,) + tuple(cwd.parents):
            if dir.joinpath(CONFIG_FILE).is_file():
                return dir
        raise ProjectNotFoundError(
            _(
                "Cannot find project root directory! {config_file} file not exists."
            ).format(config_file=CONFIG_FILE)
        )

    @property
    def project_root(self) -> Path:
        return self._locate_project_root(self.working_dir)

    @property
    def config_file(self) -> Path:
        return self.project_root.joinpath(CONFIG_FILE)

    @staticmethod
    def _detact_virtual_env(cwd: Optional[Path] = None) -> Optional[str]:
        cwd = (cwd or Path.cwd()).resolve()
        for venv_dir in cwd.iterdir():
            if venv_dir.is_dir() and (venv_dir / "pyvenv.cfg").is_file():
                return str(
                    venv_dir
                    / ("Scripts" if WINDOWS else "bin")
                    / ("python.exe" if WINDOWS else "python")
                )

    @property
    def python_path(self) -> Optional[str]:
        if python := (self._python_path or self._global_python_path):
            return python
        elif self.use_venv:
            try:
                cwd = self.project_root.resolve()
            except ProjectNotFoundError:
                cwd = Path.cwd().resolve()

            if cwd in self._path_venv_cache:
                return self._path_venv_cache[cwd]

            if venv_python := self._detact_virtual_env(cwd):
                self._path_venv_cache[cwd] = venv_python
                if self._logger:
                    self._logger.log(
                        SUCCESS,
                        _("Using python: {python_path}").format(
                            python_path=venv_python
                        ),
                    )
                return venv_python

    @property
    def use_venv(self) -> bool:
        return self._use_venv if self._use_venv is not None else self._global_use_venv

    def _get_data(self) -> TOMLDocument:
        return tomlkit.parse(self.config_file.read_text(encoding=CONFIG_FILE_ENCODING))

    def _write_data(self, data: TOMLDocument) -> None:
        self.config_file.write_text(tomlkit.dumps(data), encoding=CONFIG_FILE_ENCODING)

    def _get_nonebot_config(self, data: TOMLDocument) -> Dict[str, Any]:
        return data.get("tool", {}).get("nonebot", {})

    def get_nonebot_config(self) -> NoneBotConfig:
        return NoneBotConfig.parse_obj(self._get_nonebot_config(self._get_data()))

    def add_adapter(self, adapter: SimpleInfo) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        adapters: List[Dict[str, Any]] = table.setdefault("adapters", [])
        if all(a["module_name"] != adapter.module_name for a in adapters):
            t = tomlkit.inline_table()
            t.update(adapter.dict(include={"name", "module_name"}))
            adapters.append(t)
        self._write_data(data)

    def remove_adapter(self, adapter: SimpleInfo) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        adapters: List[Dict[str, Any]] = table.setdefault("adapters", [])
        if (
            index := next(
                (
                    i
                    for i, a in enumerate(adapters)
                    if a["module_name"] == adapter.module_name
                ),
                None,
            )
        ) is not None:
            del adapters[index]
        self._write_data(data)

    def add_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)

    def add_builtin_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("builtin_plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_builtin_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: Dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: List[str] = table.setdefault("builtin_plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)
