import sys
import json
import asyncio
from pathlib import Path
from typing import IO, Any, List, Union, Optional

from nb_cli.config import GLOBAL_CONFIG, SimpleInfo

from . import templates
from .meta import requires_python, requires_nonebot, get_nonebot_config


async def list_scripts(python_path: Optional[str] = None) -> List[str]:
    if python_path is None:
        python_path = GLOBAL_CONFIG.python

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


@requires_python
@requires_nonebot
async def run_script(
    script_name: str,
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
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
        python_path = GLOBAL_CONFIG.python

    t = templates.get_template("script/run_script.py.jinja")

    return await asyncio.create_subprocess_exec(
        python_path,
        "-c",
        t.render(
            adapters=adapters,
            builtin_plugins=builtin_plugins,
            script_name=script_name,
        ),
        cwd=cwd,
        stdin=stdin or sys.stdin,
        stdout=stdout or sys.stdout,
        stderr=stderr or sys.stderr,
    )
