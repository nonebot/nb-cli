import asyncio
from typing import IO, Any, List, Union, Optional

from .process import create_process
from .meta import requires_pip, get_default_python


@requires_pip
async def call_pip(
    pip_args: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if pip_args is None:
        pip_args = []
    if python_path is None:
        python_path = await get_default_python()

    return await create_process(
        python_path,
        "-m",
        "pip",
        *pip_args,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


@requires_pip
async def call_pip_install(
    package: Union[str, List[str]],
    pip_args: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if isinstance(package, str):
        package = [package]
    if pip_args is None:
        pip_args = []

    return await call_pip(
        ["install", *package, *pip_args],
        python_path=python_path,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


@requires_pip
async def call_pip_update(
    package: Union[str, List[str]],
    pip_args: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if isinstance(package, str):
        package = [package]
    if pip_args is None:
        pip_args = []

    return await call_pip(
        ["install", "--upgrade", *package, *pip_args],
        python_path=python_path,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


@requires_pip
async def call_pip_uninstall(
    package: Union[str, List[str]],
    pip_args: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if isinstance(package, str):
        package = [package]
    if pip_args is None:
        pip_args = []

    return await call_pip(
        ["uninstall", *package, *pip_args],
        python_path=python_path,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


@requires_pip
async def call_pip_list(
    pip_args: Optional[List[str]] = None,
    *,
    python_path: Optional[str] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    if pip_args is None:
        pip_args = []

    return await call_pip(
        ["list", *pip_args],
        python_path=python_path,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
