from typing import Optional

try:
    from pip._internal.cli.main import main as pipmain
except ImportError:
    from pip import main as pipmain


def _call_pip_install(package: str, index: Optional[str] = None):
    if index:
        return pipmain(["install", "-i", index, package])
    else:
        return pipmain(["install", package])


def _call_pip_update(package: str, index: Optional[str] = None):
    if index:
        return pipmain(["install", "--upgrade", "-i", index, package])
    else:
        return pipmain(["install", "--upgrade", package])


def _call_pip_uninstall(package: str):
    return pipmain(["uninstall", package])
