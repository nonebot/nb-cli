import sys
import json
import subprocess
from typing import List, Optional

from nb_cli.config import SimpleInfo

from . import templates
from .meta import get_config, requires_python, requires_nonebot


def list_scripts(python_path: Optional[str] = None) -> List[str]:
    if python_path is None:
        python_path = get_config().nb_cli.python

    t = templates.get_template("script/list_scripts.py.jinja")

    return json.loads(
        subprocess.check_output(
            [python_path, "-W", "ignore", "-c", t.render()], text=True
        ).strip()
    )


@requires_python
@requires_nonebot
def run_script(
    script_name: str,
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
    python_path: Optional[str] = None,
) -> subprocess.CompletedProcess[bytes]:
    if adapters is None:
        adapters = get_config().nonebot.adapters
    if builtin_plugins is None:
        builtin_plugins = get_config().nonebot.builtin_plugins
    if python_path is None:
        python_path = get_config().nb_cli.python

    t = templates.get_template("script/run_script.py.jinja")

    return subprocess.run(
        [
            python_path,
            "-c",
            t.render(
                adapters=adapters,
                builtin_plugins=builtin_plugins,
                script_name=script_name,
            ),
        ],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
