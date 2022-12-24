import sys
import json
import subprocess
from typing import List, Literal

from nb_cli.config import SimpleInfo

from . import templates


def list_scripts(python_path: str = "python") -> List[str]:
    t = templates.get_template("script/list_scripts.py.jinja")

    output = subprocess.check_output(
        [python_path, "-W", "ignore", "-c", t.render()], text=True
    )
    return json.loads(output)


def run_script(
    script_name: str,
    adapters: List[SimpleInfo],
    builtin_plugins: List[str],
    python_path: str = "python",
) -> subprocess.CompletedProcess[bytes]:
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
