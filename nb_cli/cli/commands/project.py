import re
import sys
import json
import shlex
from pathlib import Path
from logging import Logger
from functools import partial
from typing_extensions import Required
from typing import TypeAlias, TypedDict
from dataclasses import field, dataclass
from collections.abc import Sequence, MutableMapping

import click
import nonestorage
from packaging.requirements import Requirement
from noneprompt import (
    Choice,
    ListPrompt,
    InputPrompt,
    ConfirmPrompt,
    CancelledError,
    CheckboxPrompt,
)

from nb_cli import _
from nb_cli.log import ClickHandler
from nb_cli.compat import model_dump
from nb_cli.config import ConfigManager
from nb_cli.consts import DEFAULT_DRIVER
from nb_cli.cli.utils import advanced_search
from nb_cli.exceptions import ModuleLoadFailed, ProcessExecutionError
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand, run_async
from nb_cli.handlers import (
    Reloader,
    FileFilter,
    EnvironmentExecutor,
    run_project,
    list_drivers,
    list_plugins,
    list_adapters,
    create_project,
    get_project_root,
    create_virtualenv,
    terminate_process,
    generate_run_script,
    list_builtin_plugins,
    list_project_templates,
    upgrade_project_format,
    all_environment_managers,
    downgrade_project_format,
)

VALID_PROJECT_NAME = r"^[a-zA-Z][a-zA-Z0-9 _-]*$"
BLACKLISTED_PROJECT_NAME = {"nonebot", "bot"}
TEMPLATE_DESCRIPTION = {
    "bootstrap": _("bootstrap (for beginner or user)"),
    "simple": _("simple (for plugin developer)"),
}
HIDDEN_FILE_OVERRIDES = {".env", ".env.dev", ".env.prod", ".gitignore", ".vscode"}
SerializedJSON: TypeAlias = str

BLACKLISTED_PROJECT_NAME.update(sys.stdlib_module_names)


class ProjectTemplateProps(TypedDict):
    """项目模板渲染变量字典集"""

    project_name: Required[str]
    inplace: bool
    adapters: SerializedJSON
    drivers: SerializedJSON
    environment: MutableMapping[str, str]
    use_src: bool
    devtools: Sequence[str]


@dataclass
class ProjectContext:
    """项目模板生成上下文

    参数:
        variables: 模板渲染变量字典
        packages: 项目需要安装的包
    """

    variables: ProjectTemplateProps = field(  # pyright: ignore[reportAssignmentType]
        default_factory=dict
    )
    packages: list[str] = field(default_factory=list)


def project_name_validator(name: str) -> bool:
    return name == "." or (
        bool(re.match(VALID_PROJECT_NAME, name))
        and name not in BLACKLISTED_PROJECT_NAME
    )


def project_devtools_validator(devtools: tuple[Choice[str], ...]) -> bool:
    expanded = {ch.data for ch in devtools}
    return bool({"pyright", "basedpyright"} - expanded)


async def prompt_common_context(context: ProjectContext) -> ProjectContext:
    click.secho(_("Loading adapters..."))
    all_adapters = await list_adapters()
    click.secho(_("Loading drivers..."))
    all_drivers = await list_drivers()

    project_name = await InputPrompt(
        _("Project Name:"),
        validator=project_name_validator,
        error_message=_("Invalid project name!"),
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["project_name"] = project_name
    context.variables["inplace"] = False

    if project_name == ".":
        _parent_dirname = Path(".").absolute().name
        if not project_name_validator(_parent_dirname):
            click.secho(_("Invalid project name!"), fg="red")
            raise CancelledError
        if any(
            (f.name in HIDDEN_FILE_OVERRIDES or not f.name.startswith("."))
            for f in Path(project_name).iterdir()
        ):
            if not await ConfirmPrompt(
                _("Current folder is not empty. Overwrite existing files?"),
                False,
            ).prompt_async(style=CLI_DEFAULT_STYLE):
                click.echo(_("Stopped creating bot."))
                raise CancelledError
        project_name = context.variables["project_name"] = _parent_dirname
        context.variables["inplace"] = True

    confirm = False
    adapters = []
    while not confirm:
        adapters = await CheckboxPrompt(
            _("Which adapter(s) would you like to use?"),
            [
                Choice(f"{adapter.name} ({adapter.desc})", adapter)
                for adapter in all_adapters
            ],
        ).prompt_async(style=CLI_DEFAULT_STYLE)
        confirm = (
            True
            if adapters
            else await ConfirmPrompt(
                _("You haven't chosen any adapter! Please confirm."),
                default_choice=False,
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )

    _adapters = {}
    for a in adapters:
        _adapters.setdefault(a.data.project_link, []).append(model_dump(a.data))
    context.variables["adapters"] = json.dumps(_adapters)
    context.packages.extend(
        [f"{a.data.project_link}>={a.data.version}" for a in adapters]
    )

    drivers = await CheckboxPrompt(
        _("Which driver(s) would you like to use?"),
        [Choice(f"{driver.name} ({driver.desc})", driver) for driver in all_drivers],
        default_select=[
            index
            for index, driver in enumerate(all_drivers)
            if driver.name in DEFAULT_DRIVER
        ],
        validator=bool,
        error_message=_("Chosen drivers is not valid!"),
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["drivers"] = json.dumps(
        {d.data.project_link: model_dump(d.data) for d in drivers}
    )
    context.packages.extend(
        [
            f"{d.data.project_link}>={d.data.version}"
            for d in drivers
            if d.data.project_link
        ]
    )

    localstore_mode_text = [
        _("User global (default, suitable for single instance in single user)"),
        _("Current project (suitable for multiple/portable instances)"),
        _(
            "User global (isolate by project name, suitable for multiple instances in"
            " single user)"
        ),
        _("Custom storage location (for advanced users)"),
    ]

    context.variables["environment"] = {}
    localstore_mode = await ListPrompt(
        _("Which strategy of local storage would you like to use?"),
        choices=[
            Choice(localstore_mode_text[0], "global"),
            Choice(localstore_mode_text[1], "project"),
            Choice(localstore_mode_text[2], "global_isolated"),
            Choice(localstore_mode_text[3], "custom"),
        ],
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    if localstore_mode.data == "project":
        context.variables["environment"]["LOCALSTORE_USE_CWD"] = "true"
    elif localstore_mode.data == "global_isolated":
        context.variables["environment"]["LOCALSTORE_CACHE_DIR"] = shlex.quote(
            str(nonestorage.user_cache_dir(f"nonebot2-{project_name}"))
        )
        context.variables["environment"]["LOCALSTORE_DATA_DIR"] = shlex.quote(
            str(nonestorage.user_data_dir(f"nonebot2-{project_name}"))
        )
        context.variables["environment"]["LOCALSTORE_CONFIG_DIR"] = shlex.quote(
            str(nonestorage.user_config_dir(f"nonebot2-{project_name}"))
        )
    elif localstore_mode.data == "custom":
        context.variables["environment"]["LOCALSTORE_CACHE_DIR"] = shlex.quote(
            await InputPrompt(
                _("Cache directory to use:"),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )
        context.variables["environment"]["LOCALSTORE_DATA_DIR"] = shlex.quote(
            await InputPrompt(
                _("Data directory to use:"),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )
        context.variables["environment"]["LOCALSTORE_CONFIG_DIR"] = shlex.quote(
            await InputPrompt(
                _("Config directory to use:"),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )

    return context


async def prompt_simple_context(context: ProjectContext) -> ProjectContext:
    dir_name = (
        context.variables["project_name"].lower().replace(" ", "-").replace("-", "_")
    )
    src_choices: list[Choice[bool]] = [
        Choice(_('1) In a "{dir_name}" folder').format(dir_name=dir_name), False),
        Choice(_('2) In a "src" folder'), True),
    ]
    context.variables["use_src"] = (
        await ListPrompt(_("Where to store the plugin?"), src_choices).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    ).data
    context.variables["devtools"] = [
        ch.data
        for ch in await CheckboxPrompt(
            _("Which developer tool(s) would you like to use?"),
            [
                Choice("Pylance/Pyright" + _(" (Recommended)"), "pyright"),
                Choice("Ruff" + _(" (Recommended)"), "ruff"),
                Choice("MyPy", "mypy"),
                Choice("BasedPyright" + _(" (Advanced user)"), "basedpyright"),
            ],
            [0, 1],
            validator=project_devtools_validator,
            error_message=_(
                "Cannot choose 'Pylance/Pyright' and 'BasedPyright' at the same time."
            ),
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    ]

    return context


TEMPLATE_PROMPTS = {
    "simple": prompt_simple_context,
}


@click.command(
    cls=ClickAliasedCommand,
    aliases=["init"],
    context_settings={"ignore_unknown_options": True},
    help=_("Create a NoneBot project."),
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The project template to use."))
@click.option(
    "-p",
    "--python-interpreter",
    default=None,
    help=_("The python interpreter virtualenv is installed into."),
)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    output_dir: str | None,
    template: str | None,
    python_interpreter: str | None,
    pip_args: list[str] | None,
):
    if not template:
        templates = list_project_templates()
        try:
            template = (
                await ListPrompt(
                    _("Select a template to use:"),
                    [Choice(TEMPLATE_DESCRIPTION.get(t, t), t) for t in templates],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).data
        except CancelledError:
            return

    context = ProjectContext()
    try:
        context = await prompt_common_context(context)
        if inject_prompt := TEMPLATE_PROMPTS.get(template):
            context = await inject_prompt(context)
    except ModuleLoadFailed as e:
        click.secho(repr(e), fg="red")
        ctx.exit(1)
    except CancelledError:
        return

    create_project(template, {"nonebot": context.variables}, output_dir)

    try:
        install_dependencies = await ConfirmPrompt(
            _("Install dependencies now?"), default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        return

    use_venv = False
    project_dir_name = context.variables["project_name"].replace(" ", "-")
    project_dir = Path(output_dir or ".") / project_dir_name
    venv_dir = (
        Path("./.venv") if context.variables["inplace"] else project_dir / ".venv"
    )

    if install_dependencies:
        try:
            manager = await ListPrompt(
                _("Which project manager would you like to use?"),
                choices=[Choice(mgr, mgr) for mgr in await all_environment_managers()],
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            return

        if manager.data == "pip":
            try:
                use_venv = await ConfirmPrompt(
                    _("Create virtual environment?"), default_choice=True
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            except CancelledError:
                return
        else:
            use_venv = True

        if use_venv:
            click.secho(
                _("Creating virtual environment in {venv_dir} ...").format(
                    venv_dir=venv_dir
                ),
                fg="yellow",
            )
            await create_virtualenv(
                venv_dir, prompt=project_dir_name, python_path=python_interpreter
            )

        config_manager = ConfigManager(working_dir=project_dir, use_venv=use_venv)

        executor = await EnvironmentExecutor.get(
            manager.data,
            toml_manager=config_manager,
            cwd=project_dir,
            executable=config_manager.python_path,
        )
        try:
            await executor.install(
                *(Requirement(pkg) for pkg in ["nonebot2", *set(context.packages)]),
                extra_args=pip_args or (),
            )
        except ProcessExecutionError:
            click.secho(
                _(
                    "Failed to install dependencies! "
                    "You should install the dependencies manually."
                ),
                fg="red",
            )
            ctx.exit(1)

        try:
            if context.variables.get("devtools"):
                if await ConfirmPrompt(
                    _("Install developer dependencies?"), default_choice=True
                ).prompt_async(style=CLI_DEFAULT_STYLE):
                    await executor.install(
                        *(Requirement(pkg) for pkg in context.variables["devtools"]),
                        extra_args=pip_args or (),
                        dev=True,
                    )
        except CancelledError:
            pass
        except ProcessExecutionError:
            click.secho(
                _(
                    "Failed to install developer dependencies! "
                    "You may install them manually."
                ),
                fg="red",
            )

        builtin_plugins = await list_builtin_plugins(
            python_path=config_manager.python_path
        )
        try:
            loaded_builtin_plugins = [
                c.data
                for c in await CheckboxPrompt(
                    _("Which builtin plugin(s) would you like to use?"),
                    [Choice(p, p) for p in builtin_plugins],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ]
            try:
                for plugin in loaded_builtin_plugins:
                    config_manager.add_builtin_plugin(plugin)
            except Exception as e:
                click.secho(
                    _(
                        "Failed to add builtin plugins {builtin_plugins} to config: {e}"
                    ).format(builtin_plugin=loaded_builtin_plugins, e=e),
                    fg="red",
                )
        except CancelledError:
            pass

        plugins = await list_plugins()
        try:
            pending_plugins = [
                c.data
                for c in await CheckboxPrompt(
                    _("Which official plugins would you like to use?"),
                    [
                        Choice(f"{p.name} ({p.desc})", p)
                        for p in advanced_search("#official", plugins)
                    ],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ]
            if pending_plugins:
                try:
                    await executor.install(
                        *(p.as_requirement() for p in pending_plugins),
                        extra_args=pip_args or (),
                    )
                    config_manager.add_plugin(*pending_plugins)
                except ProcessExecutionError:
                    click.secho(
                        _(
                            "Failed to install plugins! "
                            "You may install the plugins manually."
                        ),
                        fg="red",
                    )
        except CancelledError:
            pass

    click.secho(_("Done!"), fg="green")
    click.secho(_("Run the following command to start your bot:"), fg="green")
    if not context.variables["inplace"]:
        click.secho(f"  cd {project_dir}", fg="green")
    click.secho("  nb run --reload", fg="green")
    ctx.exit()


@click.command(cls=ClickAliasedCommand, help=_("Generate entry file of your bot."))
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help=_("The file script saved to."),
)
@run_async
async def generate(file: str):
    content = await generate_run_script()
    Path(file).write_text(content, encoding="utf-8")


@click.command(
    cls=ClickAliasedCommand, aliases=["start"], help=_("Run the bot in current folder.")
)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help=_("Exist entry file of your bot."),
)
@click.option(
    "-r",
    "--reload",
    is_flag=True,
    default=False,
    help=_("Reload the bot when file changed."),
)
@click.option(
    "--reload-dirs",
    multiple=True,
    default=None,
    help=_("Paths to watch for changes."),
)
@click.option(
    "--reload-includes",
    multiple=True,
    default=None,
    help=_("Files to watch for changes."),
)
@click.option(
    "--reload-excludes",
    multiple=True,
    default=None,
    help=_("Files to ignore for changes."),
)
@click.option(
    "--reload-delay",
    type=float,
    default=0.5,
    show_default=True,
    help=_("Delay time for reloading in seconds."),
)
@run_async
async def run(
    file: str,
    reload: bool,
    reload_dirs: list[str] | None,
    reload_includes: list[str] | None,
    reload_excludes: list[str] | None,
    reload_delay: float,
):
    if reload:
        logger = Logger(__name__)
        logger.addHandler(ClickHandler())
        await Reloader(
            partial(run_project, exist_bot=Path(file)),
            terminate_process,
            reload_dirs=(
                [Path(i) for i in reload_dirs]
                if reload_dirs is not None
                else reload_dirs
            ),
            file_filter=FileFilter(reload_includes, reload_excludes),
            reload_delay=reload_delay,
            cwd=get_project_root(),
            logger=logger,
        ).run()
    else:
        proc = await run_project(exist_bot=Path(file))
        await proc.wait()


@click.command(
    cls=ClickAliasedCommand, help=_("Upgrade the project format of your bot.")
)
@run_async
async def upgrade_format():
    if await ConfirmPrompt(
        _("Are you sure to upgrade the project format?"), True
    ).prompt_async(style=CLI_DEFAULT_STYLE):
        await upgrade_project_format()
        click.echo(_("Successfully upgraded project format."))

    if await ConfirmPrompt(
        _("Do you want to install missing dependencies?"), True
    ).prompt_async(style=CLI_DEFAULT_STYLE):
        manager = await EnvironmentExecutor.get(cwd=get_project_root())
        await manager.lock()
        await manager.sync()


@click.command(
    cls=ClickAliasedCommand, help=_("Downgrade the project format of your bot.")
)
@run_async
async def downgrade_format():
    if await ConfirmPrompt(
        _("Are you sure to downgrade the project format?"), True
    ).prompt_async(style=CLI_DEFAULT_STYLE):
        await downgrade_project_format()
        click.echo(_("Successfully downgraded project format."))
