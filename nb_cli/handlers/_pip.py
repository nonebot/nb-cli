from typing import List, Callable, Optional

import pkg_resources

working_set = pkg_resources.working_set

entry_point = next(working_set.iter_entry_points("console_scripts", "pip"))
pipmain: Callable[[Optional[List[str]]], int] = entry_point.load()


def _call_pip_install(package: str, index: Optional[str] = None) -> int:
    if index:
        return pipmain(["install", "-i", index, package])
    else:
        return pipmain(["install", package])


def _call_pip_update(package: str, index: Optional[str] = None) -> int:
    if index:
        return pipmain(["install", "--upgrade", "-i", index, package])
    else:
        return pipmain(["install", "--upgrade", package])


def _call_pip_uninstall(package: str) -> int:
    return pipmain(["uninstall", package])
