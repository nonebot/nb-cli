from typing import Optional

from nb_cli.utils import run_script


def _call_pip_install(package: str, index: Optional[str] = None) -> int:
    if index:
        cmd = ["pip", "install", package]
    else:
        cmd = ["pip", "install", "-i", index, package]
    return run_script(cmd, call=True)


def _call_pip_update(package: str, index: Optional[str] = None) -> int:
    if index:
        cmd = ["pip", "install", "--upgrade", "-i", index, package]
    else:
        cmd = ["pip", "install", "--upgrade", package]

    return run_script(cmd, call=True)


def _call_pip_uninstall(package: str) -> int:
    return run_script(["pip", "uninstall", package], call=True)
