from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from nb_cli.consts import SCRIPTS_GROUP

templates = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(Path(__file__).parent.parent / "template" / "scripts"),
    enable_async=True,
)
templates.globals["ENTRYPOINT_GROUP"] = SCRIPTS_GROUP
templates.filters["repr"] = repr

# meta
from .meta import draw_logo as draw_logo
from .meta import requires_pip as requires_pip
from .meta import requires_python as requires_python
from .meta import load_module_data as load_module_data
from .meta import requires_nonebot as requires_nonebot
from .meta import get_default_python as get_default_python
from .meta import get_python_version as get_python_version
from .meta import get_nonebot_version as get_nonebot_version
from .meta import format_package_results as format_package_results

# isort: split

# pip
from .pip import call_pip_update as call_pip_update
from .pip import call_pip_install as call_pip_install
from .pip import call_pip_uninstall as call_pip_uninstall

# isort: split

# signal
from .signal import remove_signal_handler as remove_signal_handler
from .signal import install_signal_handler as install_signal_handler
from .signal import register_signal_handler as register_signal_handler

# isort: split

# plugin
from .plugin import list_plugins as list_plugins
from .plugin import create_plugin as create_plugin
from .plugin import list_builtin_plugins as list_builtin_plugins

# isort: split

# adapter
from .adapter import list_adapters as list_adapters
from .adapter import create_adapter as create_adapter

# isort: split

# driver
from .driver import list_drivers as list_drivers

# isort: split

# script
from .script import run_script as run_script
from .script import list_scripts as list_scripts

# isort: split

# project
from .reloader import Reloader as Reloader
from .reloader import FileFilter as FileFilter
from .project import run_project as run_project
from .project import create_project as create_project
from .project import terminate_project as terminate_project
from .project import generate_run_script as generate_run_script
from .project import list_project_templates as list_project_templates
