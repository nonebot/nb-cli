from pathlib import Path
from typing import Optional

import virtualenv

from .meta import requires_python, get_default_python


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
