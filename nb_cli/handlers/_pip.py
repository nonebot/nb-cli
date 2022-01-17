from typing import List, Callable, Optional

import httpx
import pkg_resources

working_set = pkg_resources.working_set

entry_point = next(working_set.iter_entry_points("console_scripts", "pip"))
pipmain: Callable[[Optional[List[str]]], int] = entry_point.load()


def _calling_pip_install(package: str) -> str:
    releases = list(
        httpx.get(f"https://pypi.org/pypi/{package}/json")
        .json()["releases"]
        .keys()
    )
    releases.reverse()
    for release in releases:
        requires_dist = releases = httpx.get(
            f"https://pypi.org/pypi/{package}/{release}/json"
        ).json()["info"]["requires_dist"]

        is_compatible = None
        for dist in requires_dist:
            if "nonebot2" in dist:
                is_compatible = True
                if ">=2.0.0b1" in dist or ">=2.0.0-beta.1" in dist:
                    is_compatible = False
                    break
        if is_compatible is True:
            return package + "==" + release
    raise Exception


def _call_pip_install(package: str, index: Optional[str] = None) -> int:
    package = _calling_pip_install(package)
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
