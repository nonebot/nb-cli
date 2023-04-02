import asyncio
from pathlib import Path
from typing import IO, Any, Dict, List, Union, Optional

from cookiecutter.main import cookiecutter

from nb_cli import _

from . import templates
from .config import ConfigManager
from .meta import requires_nonebot
from .process import create_process

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"


def list_project_templates() -> List[str]:
    return sorted(t.name for t in (TEMPLATE_ROOT).iterdir())


def create_project(
    project_template: str,
    context: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    no_input: bool = True,
) -> None:
    path = TEMPLATE_ROOT / project_template
    path = str(path.resolve()) if path.exists() else project_template

    cookiecutter(
        path,
        no_input=no_input,
        extra_context=context,
        output_dir=output_dir or ".",
    )


async def generate_run_script(config_manager: Optional[ConfigManager] = None) -> str:
    config = (config_manager or ConfigManager()).get_nonebot_config()

    t = templates.get_template("project/run_project.py.jinja")
    return await t.render_async(
        adapters=config.adapters, builtin_plugins=config.builtin_plugins
    )


@requires_nonebot
async def run_project(
    exist_bot: Path = Path("bot.py"),
    *,
    config_manager: Optional[ConfigManager] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    config_manager = config_manager or ConfigManager()

    cwd = config_manager.get_project_root()
    exist_bot = cwd / exist_bot

    python_path = await config_manager.get_python_path()

    if exist_bot.exists():
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
        await generate_run_script(config_manager=config_manager),
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
