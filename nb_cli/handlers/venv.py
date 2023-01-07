import os
from pathlib import Path
from typing import Dict, List, Optional

import virtualenv

from nb_cli.consts import WINDOWS

from .meta import get_default_python


async def create_virtualenv(
    venv_dir: Path,
    prompt: Optional[str] = None,
    python_interpreter: Optional[str] = None,
):
    if python_interpreter is None:
        python_interpreter = await get_default_python()

    args = ["--no-download", "--no-periodic-update", "--python", python_interpreter]

    if prompt is not None:
        args.extend(["--prompt", prompt])

    args.append(str(venv_dir))

    return virtualenv.cli_run(args)


def activate_virtualenv(
    venv_dir: Path,
    env: Optional[Dict[str, str]] = None,
    exclude: Optional[List[str]] = None,
    **kwargs: str
) -> Dict[str, str]:
    environ = os.environ if env is None else env
    exclude = [] if exclude is None else exclude
    exclude.extend(["PYTHONHOME", "__PYVENV_LAUNCHER__"])

    environ = {k: v for k, v in environ.items() if k not in exclude}
    environ.update(kwargs)

    bin_dir = venv_dir / ("Scripts" if WINDOWS else "bin")

    environ["PATH"] = os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")])
    environ["VIRTUAL_ENV"] = str(venv_dir)

    return environ
