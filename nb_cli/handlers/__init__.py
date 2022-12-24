from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from nb_cli.consts import ENTRYPOINT_GROUP

templates = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(
        Path(__file__).parent.parent / "template" / "scripts"
    ),
)
templates.globals["ENTRYPOINT_GROUP"] = ENTRYPOINT_GROUP
templates.globals["repr"] = repr

from .meta import draw_logo as draw_logo
from .script import run_script as run_script
from .project import run_project as run_project
from .script import list_scripts as list_scripts
from .project import create_project as create_project
from .project import generate_run_script as generate_run_script
from .plugin import list_builtin_plugins as list_builtin_plugins
from .project import list_project_templates as list_project_templates
