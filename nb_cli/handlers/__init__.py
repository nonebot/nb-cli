from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from nb_cli.consts import ENTRYPOINT_GROUP

templates = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(Path(__file__).parent.parent / "template" / "scripts"),
    enable_async=True,
)
templates.globals["ENTRYPOINT_GROUP"] = ENTRYPOINT_GROUP
templates.filters["repr"] = repr

from .meta import draw_logo as draw_logo
from .meta import get_config as get_config
from .reloader import Reloader as Reloader
from .script import run_script as run_script
from .meta import requires_pip as requires_pip
from .reloader import FileFilter as FileFilter
from .project import run_project as run_project
from .driver import list_drivers as list_drivers
from .plugin import list_plugins as list_plugins
from .script import list_scripts as list_scripts
from .plugin import create_plugin as create_plugin
from .adapter import list_adapters as list_adapters
from .pip import call_pip_update as call_pip_update
from .meta import requires_python as requires_python
from .pip import call_pip_install as call_pip_install
from .project import create_project as create_project
from .meta import load_module_data as load_module_data
from .meta import requires_nonebot as requires_nonebot
from .pip import call_pip_uninstall as call_pip_uninstall
from .meta import get_config_manager as get_config_manager
from .meta import get_python_version as get_python_version
from .project import terminate_project as terminate_project
from .meta import get_nonebot_version as get_nonebot_version
from .project import generate_run_script as generate_run_script
from .plugin import list_builtin_plugins as list_builtin_plugins
from .meta import format_package_results as format_package_results
from .signal import install_signal_handler as install_signal_handler
from .project import list_project_templates as list_project_templates
from .signal import register_signal_handler as register_signal_handler
