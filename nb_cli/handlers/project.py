import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import SimpleInfo

from . import templates
from .meta import get_config, requires_nonebot

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"


def list_project_templates() -> List[str]:
    return [t.name for t in (TEMPLATE_ROOT).iterdir()]


def create_project(
    project_template: str,
    context: Optional[Dict[str, Any]] = None,
    output_dir: str = ".",
    no_input: bool = True,
) -> None:
    path = TEMPLATE_ROOT / project_template
    path = str(path.resolve()) if path.exists() else project_template

    cookiecutter(
        path,
        no_input=no_input,
        extra_context=context,
        output_dir=output_dir,
    )


def generate_run_script(
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
) -> str:
    if adapters is None:
        adapters = get_config().nonebot.adapters
    if builtin_plugins is None:
        builtin_plugins = get_config().nonebot.builtin_plugins

    t = templates.get_template("project/run_project.py.jinja")
    return t.render(adapters=adapters, builtin_plugins=builtin_plugins)


@requires_nonebot
def run_project(
    adapters: Optional[List[SimpleInfo]] = None,
    builtin_plugins: Optional[List[str]] = None,
    exist_bot: Path = Path("bot.py"),
    python_path: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    if adapters is None:
        adapters = get_config().nonebot.adapters
    if builtin_plugins is None:
        builtin_plugins = get_config().nonebot.builtin_plugins
    if python_path is None:
        python_path = get_config().nb_cli.python

    if exist_bot.exists():
        return subprocess.run(
            [python_path, exist_bot],
            text=True,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    return subprocess.run(
        [
            python_path,
            "-c",
            generate_run_script(adapters=adapters, builtin_plugins=builtin_plugins),
        ],
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
