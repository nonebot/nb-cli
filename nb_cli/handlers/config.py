import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, ClassVar, Optional

import tomlkit
from pydantic import Extra, BaseModel

from nb_cli import _, cache
from nb_cli.consts import WINDOWS
from nb_cli.exceptions import PythonInterpreterError

from .store import SimpleInfo
from .venv import detect_virtualenv
from .process import create_process_shell

CONFIG_FILE = "pyproject.toml"
CONFIG_FILE_ENCODING = "utf-8"

DEFAULT_PYTHON = ("python3", "python")
WINDOWS_DEFAULT_PYTHON = ("python",)


class NoneBotConfig(BaseModel, extra=Extra.allow):
    adapters: List[SimpleInfo] = []
    plugins: List[str] = []
    plugin_dirs: List[str] = []
    builtin_plugins: List[str] = []


class ConfigManager:
    _project_root: ClassVar[Optional[Path]] = None
    _config_file: ClassVar[Optional[Path]] = None
    _python_path: ClassVar[Optional[str]] = None
    _use_venv: ClassVar[Optional[bool]] = None

    def __init__(
        self,
        *,
        project_root: Optional[Path] = None,
        config_file: Optional[Path] = None,
        python_path: Optional[str] = None,
        use_venv: Optional[bool] = None,
    ):
        self.__project_root = project_root or self._project_root
        self.config_file = config_file or self._config_file or CONFIG_FILE
        self.__python_path = python_path or self._python_path
        self.use_venv = use_venv or self._use_venv or True

    def _locate_project_root(self, cwd: Optional[Path] = None) -> Path:
        cwd = (cwd or Path.cwd()).resolve()
        for dir in (cwd,) + tuple(cwd.parents):
            if dir.joinpath(self.config_file).exists():
                return dir
        raise RuntimeError(
            _(
                "Cannot find project root directory! {config_file} file not exists."
            ).format(config_file=self.config_file)
        )

    def get_project_root(self) -> Path:
        if not self.__project_root:
            self.__project_root = self._locate_project_root()
        return self.__project_root

    @cache(ttl=None)
    async def _locate_default_python(self) -> str:
        python_to_try = WINDOWS_DEFAULT_PYTHON if WINDOWS else DEFAULT_PYTHON

        stdout = None

        for python in python_to_try:
            proc = await create_process_shell(
                f'{python} -W ignore -c "import sys, json; print(json.dumps(sys.executable))"',
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                try:
                    if executable := json.loads(stdout.strip()):
                        return executable
                except Exception:
                    continue
        raise PythonInterpreterError(
            _("Cannot find a valid Python interpreter.")
            + (f" stdout={stdout!r}" if stdout else "")
        )

    async def get_python_path(self) -> str:
        if not self.__python_path:
            if self.use_venv:
                if venv := detect_virtualenv(cwd=self.get_project_root()):
                    # TODO: log
                    self.__python_path = venv
                else:
                    self.__python_path = await self._locate_default_python()
            else:
                self.__python_path = await self._locate_default_python()
        return self.__python_path

    def get_config_file(self) -> Path:
        if (file := self.get_project_root().joinpath(CONFIG_FILE)).is_file():
            return file
        raise

    def _get_data(self) -> tomlkit.TOMLDocument:
        config_file = self.get_config_file()
        return tomlkit.parse(config_file.read_text(encoding=CONFIG_FILE_ENCODING))

    def _write_data(self, data: tomlkit.TOMLDocument) -> None:
        self.get_config_file().write_text(
            tomlkit.dumps(data), encoding=CONFIG_FILE_ENCODING
        )

    def _get_nonebot_config(self, data: tomlkit.TOMLDocument) -> Dict[str, Any]:
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
