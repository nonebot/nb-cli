import json
import asyncio
from typing import IO, Any, List, Union, Optional

from . import templates
from .config import ConfigManager
from .process import create_process
from .meta import requires_python, requires_nonebot


@requires_python
async def list_scripts(*, config_manager: Optional[ConfigManager] = None) -> List[str]:
    python_path = await (config_manager or ConfigManager()).get_python_path()

    t = templates.get_template("script/list_scripts.py.jinja")
    proc = await create_process(
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
async def run_script(
    script_name: str,
    script_args: Optional[List[str]] = None,
    *,
    config_manager: Optional[ConfigManager] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if script_args is None:
        script_args = []

    config_manager = config_manager or ConfigManager()

    cwd = config_manager.get_project_root()
    python_path = await config_manager.get_python_path()

    config = config_manager.get_nonebot_config()

    t = templates.get_template("script/run_script.py.jinja")

    return await create_process(
        python_path,
        "-c",
        await t.render_async(
            adapters=config.adapters,
            builtin_plugins=config.builtin_plugins,
            script_name=script_name,
        ),
        *script_args,
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
