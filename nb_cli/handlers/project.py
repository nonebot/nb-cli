import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import SimpleInfo

from . import templates

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"


def list_project_templates() -> List[str]:
    return [t.name for t in (TEMPLATE_ROOT).iterdir()]


def create_project(
    project_template: str,
    context: Optional[Dict[str, Any]] = None,
    output_dir: str = ".",
):
    path = TEMPLATE_ROOT / project_template
    path = str(path.resolve()) if path.exists() else project_template

    cookiecutter(
        path,
        no_input=True,
        extra_context=context,
        output_dir=output_dir,
    )


def generate_run_script(
    adapters: List[SimpleInfo], builtin_plugins: List[str]
) -> str:
    t = templates.get_template("project/run_project.py.jinja")
    return t.render(adapters=adapters, builtin_plugins=builtin_plugins)


def run_project(
    adapters: List[SimpleInfo],
    builtin_plugins: List[str],
    exist_bot: Path = Path("bot.py"),
    python_path: str = "python",
) -> subprocess.CompletedProcess[bytes]:
    if exist_bot.exists():
        return subprocess.run(
            [python_path, exist_bot],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    return subprocess.run(
        [
            python_path,
            "-c",
            generate_run_script(
                adapters=adapters, builtin_plugins=builtin_plugins
            ),
        ],
    )
