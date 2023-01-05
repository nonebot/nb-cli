import os
import sys
import signal
import asyncio
from pathlib import Path
from typing import IO, Any, Dict, List, Union, Optional

from cookiecutter.main import cookiecutter

from nb_cli.consts import WINDOWS
from nb_cli.config import SimpleInfo

from . import templates
from .meta import requires_nonebot, get_default_python, get_nonebot_config

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"


def list_project_templates() -> List[str]:
    return [t.name for t in (TEMPLATE_ROOT).iterdir()]


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


async def generate_run_script(
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
) -> str:
    bot_config = get_nonebot_config()
    if adapters is None:
        adapters = bot_config.adapters
    if builtin_plugins is None:
        builtin_plugins = bot_config.builtin_plugins

    t = templates.get_template("project/run_project.py.jinja")
    return await t.render_async(adapters=adapters, builtin_plugins=builtin_plugins)


@requires_nonebot
async def run_project(
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
    exist_bot: Path = Path("bot.py"),
    python_path: Optional[str] = None,
    cwd: Optional[Path] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    bot_config = get_nonebot_config()
    if adapters is None:
        adapters = bot_config.adapters
    if builtin_plugins is None:
        builtin_plugins = bot_config.builtin_plugins
    if python_path is None:
        python_path = await get_default_python()

    if exist_bot.exists():
        return await asyncio.create_subprocess_exec(
            python_path,
            exist_bot,
            cwd=cwd,
            stdin=stdin or sys.stdin,
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
        )

    return await asyncio.create_subprocess_exec(
        python_path,
        "-c",
        await generate_run_script(adapters=adapters, builtin_plugins=builtin_plugins),
        cwd=cwd,
        stdin=stdin or sys.stdin,
        stdout=stdout or sys.stdout,
        stderr=stderr or sys.stderr,
    )


async def terminate_project(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    if WINDOWS:
        os.kill(process.pid, signal.CTRL_C_EVENT)
    else:
        process.terminate()

    await process.wait()
