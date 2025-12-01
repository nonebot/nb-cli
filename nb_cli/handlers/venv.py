from pathlib import Path

import virtualenv

from nb_cli.config import ConfigManager

from .meta import requires_python, get_default_python


def detect_virtualenv(cwd: Path | None = None) -> str | None:
    return ConfigManager._detect_virtual_env(cwd)


@requires_python
async def create_virtualenv(
    venv_dir: Path,
    prompt: str | None = None,
    *,
    python_path: str | None = None,
):
    if python_path is None:
        python_path = await get_default_python()

    args = ["--no-download", "--no-periodic-update", "--python", python_path]

    if prompt is not None:
        args.extend(["--prompt", prompt])

    args.append(str(venv_dir))

    return virtualenv.cli_run(args)
