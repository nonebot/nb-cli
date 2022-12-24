import json
import subprocess
from typing import List

from . import templates


def list_builtin_plugins(python_path: str = "python") -> List[str]:
    t = templates.get_template("plugin/list_builtin_plugin.py.jinja")

    output = subprocess.check_output(
        [python_path, "-W", "ignore", "-c", t.render()], text=True
    )
    return json.loads(output)
