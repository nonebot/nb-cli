import sys
import subprocess
from typing import List, Optional

from .meta import get_config, requires_pip


@requires_pip
def call_pip_install(
    package: str,
    pip_args: Optional[List[str]] = None,
    python_path: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    if pip_args is None:
        pip_args = []
    if python_path is None:
        python_path = get_config().nb_cli.python

    return subprocess.run(
        [python_path, "-m", "pip", "install", package, *pip_args],
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


@requires_pip
def call_pip_update(
    package: str,
    pip_args: Optional[List[str]] = None,
    python_path: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    if pip_args is None:
        pip_args = []
    if python_path is None:
        python_path = get_config().nb_cli.python

    return subprocess.run(
        [python_path, "-m", "pip", "install", "--upgrade", package, *pip_args],
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


@requires_pip
def call_pip_uninstall(
    package: str,
    pip_args: Optional[List[str]] = None,
    python_path: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    if pip_args is None:
        pip_args = []
    if python_path is None:
        python_path = get_config().nb_cli.python

    return subprocess.run(
        [python_path, "-m", "pip", "uninstall", package, *pip_args],
        text=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
