from pathlib import Path
from typing import Optional

import virtualenv

from nb_cli.consts import WINDOWS

from .meta import requires_python, get_default_python


def detect_virtualenv(cwd: Optional[Path] = None) -> Optional[str]:
    cwd = (cwd or Path.cwd()).resolve()
    for venv_dir in cwd.iterdir():
        if venv_dir.is_dir() and (venv_dir / "pyvenv.cfg").is_file():
            return str(
                venv_dir
                / ("Scripts" if WINDOWS else "bin")
                / ("python.exe" if WINDOWS else "python")
            )


@requires_python
async def create_virtualenv(
    venv_dir: Path,
    prompt: Optional[str] = None,
    *,
    python_path: Optional[str] = None,
):
    if python_path is None:
        python_path = await get_default_python()

    args = ["--no-download", "--no-periodic-update", "--python", python_path]

    if prompt is not None:
        args.extend(["--prompt", prompt])

    args.append(str(venv_dir))

    return virtualenv.cli_run(args)
