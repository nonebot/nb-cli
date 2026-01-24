import string
import logging
import weakref
import functools
from pathlib import Path
from collections.abc import Generator
from abc import ABCMeta, abstractmethod
from typing import Any, Generic, TypeVar, ClassVar, overload
from contextlib import AbstractContextManager, contextmanager

import click
import tomlkit
import tomlkit.items
import tomlkit.container
from packaging.requirements import Requirement
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
_T = TypeVar("_T")
_U = TypeVar("_U")


def _merge_package_requirements(
    base: Requirement, override: Requirement
) -> Requirement:
    assert base.name == override.name, "Cannot merge different package requirements."
    name = base.name
    specs = override.specifier if override.specifier else base.specifier
    extras = sorted(base.extras | override.extras)
    marker = override.marker or base.marker
    new_req_str = name
    if extras:
        new_req_str += "[" + ",".join(extras) + "]"
    if specs:
        new_req_str += "".join(str(s) for s in specs)
    if marker:
        new_req_str += f"; {marker}"
    return Requirement(new_req_str)


def _remove_package_requirements(
    base: Requirement, remove: Requirement
) -> Requirement | None:
    assert base.name == remove.name, "Cannot remove different package requirements."
    if not remove.extras:
        return None
    name = base.name
    specs = base.specifier
    extras = base.extras - remove.extras
    marker = base.marker
    new_req_str = name
    if extras:
        new_req_str += "[" + ",".join(sorted(extras)) + "]"
    if specs:
        new_req_str += "".join(str(s) for s in specs)
    if marker:
        new_req_str += f"; {marker}"
    return Requirement(new_req_str)


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
    def add_adapter(ctx: Any, adapter: PackageInfo | SimpleInfo) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def remove_adapter(ctx: Any, adapter: PackageInfo | SimpleInfo) -> bool:
        """
        删除适配器的文档体操作。

        Returns:
            bool: 表示是否可以执行卸载操作
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def add_plugin(ctx: Any, plugin: PackageInfo | str) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def remove_plugin(ctx: Any, plugin: PackageInfo | str) -> bool:
        """
        删除插件的文档体操作。

        Returns:
            bool: 表示是否可以执行卸载操作
        """
        raise NotImplementedError


class ConfigManager:
    _global_working_dir: ClassVar[Path | None] = None
    _global_python_path: ClassVar[str | None] = None
    _global_use_venv: ClassVar[bool] = True
    _path_venv_cache: ClassVar[dict[Path, str | None]] = {}
    _policy: _ConfigPolicy[Any]

    def __init__(
        self,
        *,
        working_dir: Path | None = None,
        python_path: str | None = None,
        use_venv: bool | None = None,
        logger: logging.Logger | None = None,
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
    def _locate_project_root(cwd: Path | None = None) -> Path:
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
    def _detect_virtual_env(cwd: Path | None = None) -> str | None:
        cwd = (cwd or Path.cwd()).resolve()
        for venv_dir in cwd.iterdir():
            if venv_dir.is_dir() and (venv_dir / "pyvenv.cfg").is_file():
                return str(
                    venv_dir
                    / ("Scripts" if WINDOWS else "bin")
                    / ("python.exe" if WINDOWS else "python")
                )

    @property
    def python_path(self) -> str | None:
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

    @overload
    def _data_context(
        self, domain: str, default_: Any, subdomain: str, sub_default: _U
    ) -> AbstractContextManager[_U, None]: ...

    @overload
    def _data_context(
        self, domain: str, default_: Any, subdomain: str, sub_default: None = None
    ) -> AbstractContextManager[
        tomlkit.items.Item | tomlkit.container.Container, None
    ]: ...

    @overload
    def _data_context(
        self, domain: str, default_: _T, subdomain: None = None
    ) -> AbstractContextManager[_T, None]: ...

    @overload
    def _data_context(
        self, domain: str, default_: None = None, subdomain: None = None
    ) -> AbstractContextManager[
        tomlkit.items.Item | tomlkit.container.Container, None
    ]: ...

    @overload
    def _data_context(
        self, domain: None = None
    ) -> AbstractContextManager[TOMLDocument, None]: ...

    @contextmanager
    def _data_context(
        self,
        domain: str | None = None,
        default_: _T | None = None,
        subdomain: str | None = None,
        sub_default: _U | None = None,
    ) -> Generator[
        _T | _U | TOMLDocument | tomlkit.items.Item | tomlkit.container.Container,
        Any,
        None,
    ]:
        table = self._get_data()

        if domain is None:
            yield table
        elif default_ is None:
            yield table[domain]
        else:
            data = table.setdefault(domain, default_)
            if subdomain is None:
                yield data
            elif sub_default is None:
                yield data[subdomain]
            else:
                yield data.setdefault(subdomain, sub_default)

        self._write_data(table)

    def _get_nonebot_config(self, data: TOMLDocument) -> dict[str, Any]:
        return data.get("tool", {}).get("nonebot", {})

    def get_nonebot_config(self) -> NoneBotConfig | LegacyNoneBotConfig:
        return self.policy.get_nonebot_config()

    def update_nonebot_config(
        self, config: NoneBotConfig | LegacyNoneBotConfig
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

    def get_dependencies(self, *, group: str | None = None) -> list[Requirement]:
        data = self._get_data()
        if group is None:
            deps: list[str] = data.setdefault("project", {}).setdefault(
                "dependencies", []
            )
        else:
            deps: list[str] = (
                data.setdefault("project", {})
                .setdefault("dependency-groups", {})
                .setdefault(group, [])
            )
        return [Requirement(d) for d in deps]

    def add_dependency(
        self, *dependencies: str | PackageInfo | Requirement, group: str | None = None
    ) -> None:
        if not dependencies:
            return

        deps = self.get_dependencies(group=group)
        with self._data_context("project", dict[str, Any]()) as project:
            for dependency in dependencies:
                depinfo = (
                    Requirement(
                        dependency
                        if isinstance(dependency, str)
                        else dependency.as_dependency(versioned=False)
                    )
                    if isinstance(dependency, (str, PackageInfo))
                    else dependency
                )
                matches = [i for i, d in enumerate(deps) if d.name == depinfo.name]

                if matches:
                    idx = matches[0]
                    deps[idx] = functools.reduce(
                        _merge_package_requirements, (deps[i] for i in matches)
                    )

                    for i in sorted(matches[1:], reverse=True):
                        del deps[i]

                    deps[idx] = _merge_package_requirements(deps[idx], depinfo)
                else:
                    depinfo = (
                        Requirement(
                            dependency
                            if isinstance(dependency, str)
                            else dependency.as_dependency(versioned=True)
                        )
                        if isinstance(dependency, (str, PackageInfo))
                        else dependency
                    )
                    deps.append(depinfo)

            if group is None:
                project["dependencies"] = tomlkit.array().multiline(True)
                project["dependencies"].extend(str(d) for d in deps)
            else:
                project["dependency-groups"] = tomlkit.table()
                gdep = tomlkit.array().multiline(True)
                gdep.extend(str(d) for d in deps)
                project["dependency-groups"].add(group, gdep)

    def update_dependency(self, *dependencies: PackageInfo | Requirement) -> None:
        if not dependencies:
            return

        deps = self.get_dependencies()
        with self._data_context("project", dict[str, Any]()) as project:
            for dependency in dependencies:
                depinfo = (
                    Requirement(dependency.as_dependency(versioned=True))
                    if isinstance(dependency, PackageInfo)
                    else dependency
                )
                matches = [i for i, d in enumerate(deps) if d.name == depinfo.name]

                if matches:
                    idx = matches[0]
                    deps[idx] = functools.reduce(
                        _merge_package_requirements, (deps[i] for i in matches)
                    )

                    for i in sorted(matches[1:], reverse=True):
                        del deps[i]

                    deps[idx] = _merge_package_requirements(deps[idx], depinfo)
                else:
                    deps.append(depinfo)

            project["dependencies"] = tomlkit.array().multiline(True)
            project["dependencies"].extend(str(d) for d in deps)

    def remove_dependency(
        self, *dependencies: str | PackageInfo | Requirement
    ) -> list[Requirement]:
        """
        删除依赖记录操作。

        Returns:
            list[Requirement]: 成功完整移除的相关依赖。
        """
        if not dependencies:
            return []

        removables: list[Requirement] = []

        deps = self.get_dependencies()
        with self._data_context("project", dict[str, Any]()) as project:
            for dependency in dependencies:
                status = True
                depinfo = (
                    Requirement(
                        dependency
                        if isinstance(dependency, str)
                        else dependency.as_dependency(versioned=False)
                    )
                    if isinstance(dependency, (str, PackageInfo))
                    else dependency
                )

                def _convert(d: Requirement) -> Requirement | None:
                    nonlocal status
                    if d.name != depinfo.name:
                        return d
                    res = _remove_package_requirements(d, depinfo)
                    status *= res is None
                    return res

                deps = [d for d in (_convert(d) for d in deps) if d is not None]
                if status:
                    removables.append(depinfo)

            project["dependencies"] = tomlkit.array().multiline(True)
            project["dependencies"].extend(str(d) for d in deps)

        return removables

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
        return isinstance(cfg.get("adapters", {}), dict) and isinstance(
            cfg.get("plugins", {}), dict
        )

    def get_nonebot_config(self) -> NoneBotConfig:
        return type_validate_python(
            NoneBotConfig, self.origin._get_nonebot_config(self.origin._get_data())
        )

    @staticmethod
    def add_adapter(
        ctx: dict[str, list[dict[str, str]]], adapter: PackageInfo | SimpleInfo
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
        ctx: dict[str, list[dict[str, str]]], adapter: PackageInfo | SimpleInfo
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
    def add_plugin(ctx: dict[str, list[str]], plugin: PackageInfo | str) -> None:
        plugin_data = ctx.setdefault(
            "@local" if isinstance(plugin, str) else plugin.project_link, []
        )
        name = plugin if isinstance(plugin, str) else plugin.module_name
        if name not in plugin_data:
            plugin_data.append(name)

    @staticmethod
    def remove_plugin(ctx: dict[str, list[str]], plugin: PackageInfo | str) -> bool:
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
        result = isinstance(cfg.get("adapters", []), list) and isinstance(
            cfg.get("plugins", []), list
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
    def add_plugin(ctx: list[str], plugin: SimpleInfo | str) -> None:
        plugin_ = plugin if isinstance(plugin, str) else plugin.module_name
        if plugin_ not in ctx:
            ctx.append(plugin_)

    @staticmethod
    def remove_plugin(ctx: list[str], plugin: SimpleInfo | str) -> bool:
        plugin_ = plugin if isinstance(plugin, str) else plugin.module_name
        if plugin_ in ctx:
            ctx.remove(plugin_)
        return True
