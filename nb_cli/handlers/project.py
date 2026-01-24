import asyncio
from pathlib import Path
from typing import IO, Any, TypeVar
from collections.abc import Iterable

import click
from cookiecutter.main import cookiecutter

from nb_cli import _
from nb_cli.config import SimpleInfo, PackageInfo, NoneBotConfig, LegacyNoneBotConfig

from . import templates
from .driver import list_drivers
from .plugin import list_plugins
from .adapter import list_adapters
from .process import create_process
from .meta import (
    get_project_root,
    requires_nonebot,
    get_config_manager,
    get_default_python,
    get_nonebot_config,
    requires_project_root,
)

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"

T_info = TypeVar("T_info", bound=PackageInfo)


def list_project_templates() -> list[str]:
    return sorted(t.name for t in (TEMPLATE_ROOT).iterdir())


def create_project(
    project_template: str,
    context: dict[str, Any] | None = None,
    output_dir: str | None = None,
    no_input: bool = True,
) -> None:
    path = TEMPLATE_ROOT / project_template
    path = str(path.resolve()) if path.exists() else project_template

    cookiecutter(
        path,
        no_input=no_input,
        extra_context=context,
        output_dir=output_dir or ".",
        overwrite_if_exists=True,
    )


async def generate_run_script(
    adapters: list[SimpleInfo] | None = None,
    builtin_plugins: list[str] | None = None,
) -> str:
    # only read global config when no data provided
    if adapters is None or builtin_plugins is None:
        bot_config = get_nonebot_config()
        if adapters is None:
            adapters = bot_config.get_adapters()
        if builtin_plugins is None:
            builtin_plugins = bot_config.builtin_plugins

    t = templates.get_template("project/run_project.py.jinja")
    return await t.render_async(adapters=adapters, builtin_plugins=builtin_plugins)


@requires_project_root
@requires_nonebot
async def run_project(
    adapters: list[SimpleInfo] | None = None,
    builtin_plugins: list[str] | None = None,
    exist_bot: Path = Path("bot.py"),
    *,
    python_path: str | None = None,
    cwd: Path | None = None,
    stdin: IO[Any] | int | None = None,
    stdout: IO[Any] | int | None = None,
    stderr: IO[Any] | int | None = None,
) -> asyncio.subprocess.Process:
    # only read global config when no data provided
    if adapters is None or builtin_plugins is None:
        bot_config = get_nonebot_config()
        if adapters is None:
            adapters = bot_config.get_adapters()
        if builtin_plugins is None:
            builtin_plugins = bot_config.builtin_plugins

    if python_path is None:
        python_path = await get_default_python()
    if cwd is None:
        cwd = get_project_root()

    if cwd.joinpath(exist_bot).exists():
        return await create_process(
            python_path,
            exist_bot,
            cwd=cwd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )

    return await create_process(
        python_path,
        "-c",
        await generate_run_script(adapters=adapters, builtin_plugins=builtin_plugins),
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


def _index_by_module_name(data: Iterable[T_info]) -> dict[str, T_info]:
    res: dict[str, T_info] = {}

    for d in data:
        res[d.module_name] = d

    return res


@requires_project_root
async def upgrade_project_format(*, cwd: Path | None = None) -> None:
    bot_config = get_nonebot_config(cwd)
    if isinstance(bot_config, NoneBotConfig):
        click.echo(_("Current format is already the new format."))
        return

    all_adapters = _index_by_module_name(await list_adapters())
    all_plugins = _index_by_module_name(await list_plugins())
    nonebot_pkg = next(iter(await list_drivers("~none"))).model_copy()
    nonebot_pkg.project_link = "nonebot2"

    new_adapters: dict[str, list[SimpleInfo]] = {"@local": []}
    new_plugins: dict[str, list[str]] = {"@local": []}

    packages: list[PackageInfo] = []

    for a in bot_config.adapters:
        if a.module_name in all_adapters:
            adapter = all_adapters[a.module_name]
            packages.append(adapter)
            info = SimpleInfo(name=adapter.name, module_name=adapter.module_name)
            if adapter.name != a.name:
                click.secho(
                    _("WARNING: Inconsistent adapter name info: {old!r} -> {new!r}"),
                    fg="yellow",
                )
        else:
            info = a
        new_adapters.setdefault(
            (
                all_adapters[a.module_name].project_link
                if a.module_name in all_adapters
                else "@local"
            ),
            [],
        ).append(info)

    for p in bot_config.plugins:
        if p in all_plugins:
            packages.append(all_plugins[p])
        new_plugins.setdefault(
            (all_plugins[p].project_link if p in all_plugins else "@local"), []
        ).append(p)

    new_config = NoneBotConfig(
        adapters=new_adapters,
        plugins=new_plugins,
        plugin_dirs=bot_config.plugin_dirs,
        builtin_plugins=bot_config.builtin_plugins,
    )

    manager = get_config_manager(cwd)
    manager.update_nonebot_config(new_config)
    manager.add_dependency(nonebot_pkg, *packages)


@requires_project_root
async def downgrade_project_format(*, cwd: Path | None = None) -> None:
    bot_config = get_nonebot_config(cwd)
    if isinstance(bot_config, LegacyNoneBotConfig):
        click.echo(_("Current format is already the old format."))
        return

    old_config = LegacyNoneBotConfig(
        adapters=bot_config.get_adapters(),
        plugins=bot_config.get_plugins(),
        plugin_dirs=bot_config.plugin_dirs,
        builtin_plugins=bot_config.builtin_plugins,
    )

    manager = get_config_manager(cwd)
    manager.update_nonebot_config(old_config)
