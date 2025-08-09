import string
import logging
import weakref
import functools
from pathlib import Path
from abc import ABCMeta, abstractmethod
from typing import Any, Union, Generic, TypeVar, ClassVar, Optional

import click
import tomlkit
from tomlkit.toml_document import TOMLDocument

from nb_cli import _
from nb_cli.log import SUCCESS
from nb_cli.consts import WINDOWS
from nb_cli.compat import model_dump, type_validate_python
from nb_cli.exceptions import ProjectInvalidError, ProjectNotFoundError

from .model import SimpleInfo, PackageInfo, NoneBotConfig, LegacyNoneBotConfig

CONFIG_FILE = "pyproject.toml"
CONFIG_FILE_ENCODING = "utf-8"

VALID_PACKAGE_NAME_CHARS = string.ascii_letters + string.digits + "-_"

_T_config = TypeVar("_T_config", NoneBotConfig, LegacyNoneBotConfig)


@functools.lru_cache(maxsize=512)
def _split_package_dependency(dep: str) -> tuple[str, Optional[str], Optional[str]]:
    pkg_delims = ("=", ">", "<", "!", "~", ";")
    sep = min(
        filter(lambda i: i != -1, (dep.find(ch) for ch in pkg_delims)), default=len(dep)
    )
    cons = dep[sep:]
    ver, env = cons.split(";", maxsplit=1) if ";" in cons else (cons, None)
    return (
        dep[:sep].strip(),
        ver.strip() or None,
        env.strip() if env is not None else None,
    )


class _ConfigPolicy(Generic[_T_config], metaclass=ABCMeta):
    policies: ClassVar[list[type["_ConfigPolicy[Any]"]]] = []

    def __init__(self, origin: "ConfigManager"):
        self._origin = weakref.ref(origin)

    def __init_subclass__(cls) -> None:
        cls.policies.append(cls)

    @property
    def origin(self) -> "ConfigManager":
        if origin_ := self._origin():
            return origin_
        raise ReferenceError("Cannot get ConfigManager origin.")

    @staticmethod
    @abstractmethod
    def test_format(cfg: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_nonebot_config(self) -> _T_config:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def add_adapter(ctx: Any, adapter: Union[PackageInfo, SimpleInfo]) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def remove_adapter(ctx: Any, adapter: Union[PackageInfo, SimpleInfo]) -> bool:
        """
        删除适配器的文档体操作。

        Returns:
            bool: 表示是否可以执行卸载操作
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def add_plugin(ctx: Any, plugin: Union[PackageInfo, str]) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def remove_plugin(ctx: Any, plugin: Union[PackageInfo, str]) -> bool:
        """
        删除插件的文档体操作。

        Returns:
            bool: 表示是否可以执行卸载操作
        """
        raise NotImplementedError


class ConfigManager:
    _global_working_dir: ClassVar[Optional[Path]] = None
    _global_python_path: ClassVar[Optional[str]] = None
    _global_use_venv: ClassVar[bool] = True
    _path_venv_cache: ClassVar[dict[Path, Optional[str]]] = {}
    _policy: _ConfigPolicy[Any]

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
    def policy(self) -> _ConfigPolicy[Any]:
        if not hasattr(self, "_policy"):
            self._policy = self._select_policy()
        return self._policy

    @property
    def working_dir(self) -> Path:
        return (self._working_dir or self._global_working_dir or Path.cwd()).resolve()

    def _select_policy(self) -> _ConfigPolicy[Any]:
        cfg = self._get_nonebot_config(self._get_data())
        if isinstance(cfg.setdefault("plugin_dirs", []), list) and isinstance(
            cfg.setdefault("builtin_plugins", []), list
        ):
            for policy in _ConfigPolicy.policies:
                if policy.test_format(cfg):
                    return policy(self)
        raise ProjectInvalidError(_("Invalid project config format."))

    @staticmethod
    def _locate_project_root(cwd: Optional[Path] = None) -> Path:
        cwd = (cwd or Path.cwd()).resolve()
        for dir in (cwd, *cwd.parents):
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
    def _detect_virtual_env(cwd: Optional[Path] = None) -> Optional[str]:
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

            if venv_python := self._detect_virtual_env(cwd):
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

    def _get_nonebot_config(self, data: TOMLDocument) -> dict[str, Any]:
        return data.get("tool", {}).get("nonebot", {})

    def get_nonebot_config(self) -> Union[NoneBotConfig, LegacyNoneBotConfig]:
        return self.policy.get_nonebot_config()

    def update_nonebot_config(
        self, config: Union[NoneBotConfig, LegacyNoneBotConfig]
    ) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        if isinstance(config, NoneBotConfig):
            table["adapters"] = {}
            for p, s in config.adapters.items():
                table["adapters"][p] = []
                for a in s:
                    t = tomlkit.inline_table()
                    t.update(model_dump(a, include={"name", "module_name"}))
                    table["adapters"][p].append(t)
        elif isinstance(config, LegacyNoneBotConfig):
            table["adapters"] = []
            for a in config.adapters:
                t = tomlkit.inline_table()
                t.update(model_dump(a, include={"name", "module_name"}))
                table["adapters"].append(t)
        else:
            raise ValueError(f"Invalid config: {config!r}")
        table["plugins"] = config.plugins
        table["plugin_dirs"] = config.plugin_dirs
        table["builtin_plugins"] = config.builtin_plugins
        self._write_data(data)
        self._policy = self._select_policy()  # update access policy

    def add_dependency(self, *dependencies: Union[str, PackageInfo]) -> None:
        if not dependencies:
            return
        data = self._get_data()
        deps: list[str] = data.setdefault("project", {}).setdefault("dependencies", [])

        for dependency in dependencies:
            dep_str = (
                dependency if isinstance(dependency, str) else dependency.project_link
            )

            if not any(
                _split_package_dependency(d)[0] == _split_package_dependency(dep_str)[0]
                for d in deps
            ):
                if isinstance(dependency, str):
                    deps.append(dep_str)
                else:
                    deps.append(f"{dep_str}>={dependency.version}")

        self._write_data(data)

    def update_dependency(self, *dependencies: PackageInfo) -> None:
        data = self._get_data()
        deps: list[str] = data.setdefault("project", {}).setdefault("dependencies", [])

        for dependency in dependencies:
            dep_str = dependency.project_link
            matches = [
                (i, d)
                for i, d in enumerate(deps)
                if _split_package_dependency(d)[0]
                == _split_package_dependency(dep_str)[0]
            ]

            if matches:
                idx, _ = matches[0]
                deps[idx] = f"{dep_str}>={dependency.version}"

                for i, _ in sorted(matches[1:], reverse=True):
                    del deps[i]
            else:
                deps.append(f"{dep_str}>={dependency.version}")

        self._write_data(data)

    def remove_dependency(self, *dependencies: Union[str, PackageInfo]) -> None:
        data = self._get_data()
        deps: list[str] = data.setdefault("project", {}).setdefault("dependencies", [])

        for dependency in dependencies:
            dep_str = (
                dependency if isinstance(dependency, str) else dependency.project_link
            )
            indices_to_remove = [
                i
                for i, d in enumerate(deps)
                if _split_package_dependency(d)[0]
                == _split_package_dependency(dep_str)[0]
            ]

            for i in sorted(indices_to_remove, reverse=True):
                del deps[i]

        self._write_data(data)

    def add_adapter(self, *adapters: PackageInfo) -> None:
        if not adapters:
            return
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        tb_adapters: dict[str, list[dict[str, str]]] = table.setdefault("adapters", {})
        for adapter in adapters:
            self.policy.add_adapter(tb_adapters, adapter)
        self._write_data(data)

    def remove_adapter(self, adapter: PackageInfo) -> bool:
        """
        删除适配器操作。

        Returns:
            bool: 表示是否可以执行卸载操作。
        """
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        adapters: dict[str, list[dict[str, str]]] = table.setdefault("adapters", {})
        can_remove = self.policy.remove_adapter(adapters, adapter)
        self._write_data(data)
        return can_remove

    def add_plugin(self, *plugins: PackageInfo) -> None:
        if not plugins:
            return
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        tb_plugins: dict[str, list[str]] = table.setdefault("plugins", {})
        for plugin in plugins:
            self.policy.add_plugin(tb_plugins, plugin)
        self._write_data(data)

    def remove_plugin(self, plugin: PackageInfo) -> bool:
        """
        删除插件操作。

        Returns:
            bool: 表示是否可以执行卸载操作。
        """
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: dict[str, list[str]] = table.setdefault("plugins", {})
        can_remove = self.policy.remove_plugin(plugins, plugin)
        self._write_data(data)
        return can_remove

    def add_builtin_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: list[str] = table.setdefault("builtin_plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_builtin_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("tool", {}).setdefault("nonebot", {})
        plugins: list[str] = table.setdefault("builtin_plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)


class DefaultConfigPolicy(_ConfigPolicy[NoneBotConfig]):
    @staticmethod
    def test_format(cfg: dict[str, Any]) -> bool:
        return isinstance(cfg.setdefault("adapters", {}), dict) and isinstance(
            cfg.setdefault("plugins", {}), dict
        )

    def get_nonebot_config(self) -> NoneBotConfig:
        return type_validate_python(
            NoneBotConfig, self.origin._get_nonebot_config(self.origin._get_data())
        )

    @staticmethod
    def add_adapter(
        ctx: dict[str, list[dict[str, str]]], adapter: Union[PackageInfo, SimpleInfo]
    ) -> None:
        adapter_data = ctx.setdefault(
            adapter.project_link if isinstance(adapter, PackageInfo) else "@local", []
        )
        if all(a["module_name"] != adapter.module_name for a in adapter_data):
            t = tomlkit.inline_table()
            t.update(model_dump(adapter, include={"name", "module_name"}))
            adapter_data.append(t)

    @staticmethod
    def remove_adapter(
        ctx: dict[str, list[dict[str, str]]], adapter: Union[PackageInfo, SimpleInfo]
    ) -> bool:
        if isinstance(adapter, PackageInfo) and adapter.project_link not in ctx:
            return True
        adapter_data = ctx.setdefault(
            adapter.project_link if isinstance(adapter, PackageInfo) else "@local", []
        )
        if (
            index := next(
                (
                    i
                    for i, a in enumerate(adapter_data)
                    if a["module_name"] == adapter.module_name
                ),
                None,
            )
        ) is not None:
            del adapter_data[index]
        if isinstance(adapter, PackageInfo) and not adapter_data:
            del ctx[adapter.project_link]
            return True
        return False

    @staticmethod
    def add_plugin(ctx: dict[str, list[str]], plugin: Union[PackageInfo, str]) -> None:
        plugin_data = ctx.setdefault(
            "@local" if isinstance(plugin, str) else plugin.project_link, []
        )
        if plugin not in plugin_data:
            plugin_data.append(
                plugin if isinstance(plugin, str) else plugin.module_name
            )

    @staticmethod
    def remove_plugin(
        ctx: dict[str, list[str]], plugin: Union[PackageInfo, str]
    ) -> bool:
        if isinstance(plugin, PackageInfo) and plugin.project_link not in ctx:
            return True
        plugin_data = ctx.setdefault(
            "@local" if isinstance(plugin, str) else plugin.project_link, []
        )
        if (plugin if isinstance(plugin, str) else plugin.module_name) in plugin_data:
            plugin_data.remove(
                plugin if isinstance(plugin, str) else plugin.module_name
            )
        if isinstance(plugin, PackageInfo) and not plugin_data:
            del ctx[plugin.project_link]
            return True
        return False


class LegacyConfigPolicy(_ConfigPolicy[LegacyNoneBotConfig]):
    @staticmethod
    def test_format(cfg: dict[str, Any]) -> bool:
        result = isinstance(cfg.setdefault("adapters", []), list) and isinstance(
            cfg.setdefault("plugins", []), list
        )
        if result:
            click.secho(
                _(
                    "WARNING: Legacy configuration format detected.\n"
                    "*** Use `nb upgrade-format` to upgrade to the new format."
                ),
                fg="yellow",
            )
        return result

    def get_nonebot_config(self) -> LegacyNoneBotConfig:
        return type_validate_python(
            LegacyNoneBotConfig,
            self.origin._get_nonebot_config(self.origin._get_data()),
        )

    @staticmethod
    def add_adapter(ctx: list[dict[str, Any]], adapter: SimpleInfo) -> None:
        if all(a["module_name"] != adapter.module_name for a in ctx):
            t = tomlkit.inline_table()
            t.update(model_dump(adapter, include={"name", "module_name"}))
            ctx.append(t)

    @staticmethod
    def remove_adapter(ctx: list[dict[str, Any]], adapter: SimpleInfo) -> bool:
        if (
            index := next(
                (
                    i
                    for i, a in enumerate(ctx)
                    if a["module_name"] == adapter.module_name
                ),
                None,
            )
        ) is not None:
            del ctx[index]
        return True

    @staticmethod
    def add_plugin(ctx: list[str], plugin: Union[SimpleInfo, str]) -> None:
        plugin_ = plugin if isinstance(plugin, str) else plugin.module_name
        if plugin_ not in ctx:
            ctx.append(plugin_)

    @staticmethod
    def remove_plugin(ctx: list[str], plugin: Union[SimpleInfo, str]) -> bool:
        plugin_ = plugin if isinstance(plugin, str) else plugin.module_name
        if plugin_ in ctx:
            ctx.remove(plugin_)
        return True
