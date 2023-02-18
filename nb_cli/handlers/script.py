import json
import asyncio
from pathlib import Path
from typing import IO, Any, List, Union, Optional

from nb_cli.config import SimpleInfo

from . import templates
from .meta import (
    requires_python,
    requires_nonebot,
    get_default_python,
    get_nonebot_config,
    ensure_process_terminated,
)


@requires_python
async def list_scripts(*, python_path: Optional[str] = None) -> List[str]:
    if python_path is None:
        python_path = await get_default_python()

    t = templates.get_template("script/list_scripts.py.jinja")
    proc = await asyncio.create_subprocess_exec(
        python_path,
        "-W",
        "ignore",
        "-c",
        await t.render_async(),
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return json.loads(stdout.strip())


@requires_nonebot
@ensure_process_terminated
async def run_script(
    script_name: str,
    script_args: Optional[List[str]] = None,
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    cwd: Optional[Path] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if script_args is None:
        script_args = []

    bot_config = get_nonebot_config()
    if adapters is None:
        adapters = bot_config.adapters
    if builtin_plugins is None:
        builtin_plugins = bot_config.builtin_plugins
    if python_path is None:
        python_path = await get_default_python()

    t = templates.get_template("script/run_script.py.jinja")

    return await asyncio.create_subprocess_exec(
        python_path,
        "-c",
        await t.render_async(
            adapters=adapters,
            builtin_plugins=builtin_plugins,
            script_name=script_name,
        ),
        *script_args,
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
