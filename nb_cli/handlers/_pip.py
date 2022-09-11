from typing import Optional

from nb_cli.utils import run_script


def _call_pip_install(
    package: str, index: Optional[str] = None, python_path: str = "python"
) -> int:
    if index:
        cmd = [python_path, "-m", "pip", "install", package]
    else:
        cmd = [python_path, "-m", "pip", "install", "-i", index, package]
    return run_script(cmd, call=True)


def _call_pip_update(
    package: str, index: Optional[str] = None, python_path: str = "python"
) -> int:
    if index:
        cmd = [
            python_path,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-i",
            index,
            package,
        ]
    else:
        cmd = [python_path, "-m", "pip", "install", "--upgrade", package]

    return run_script(cmd, call=True)


def _call_pip_uninstall(package: str, python_path: str = "python") -> int:
    return run_script(
        [python_path, "-m", "pip", "uninstall", package], call=True
    )
