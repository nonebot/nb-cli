import os
import signal
import asyncio
import subprocess
from pathlib import Path
from functools import wraps
from contextlib import nullcontext
from typing_extensions import ParamSpec
from typing import IO, Any, Set, Union, Callable, Optional, Coroutine

from nb_cli.consts import WINDOWS

from .signal import shield_signals, remove_signal_handler, register_signal_handler

P = ParamSpec("P")


def ensure_process_terminated(
    func: Callable[P, Coroutine[Any, Any, asyncio.subprocess.Process]]
) -> Callable[P, Coroutine[Any, Any, asyncio.subprocess.Process]]:
    tasks: Set[asyncio.Task] = set()

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> asyncio.subprocess.Process:
        should_exit = asyncio.Event()

        def shutdown(signum, frame):
            should_exit.set()

        register_signal_handler(shutdown)

        async def wait_for_exit():
            await should_exit.wait()
            await terminate_process(proc)

        async def wait_for_finish():
            await proc.wait()
            should_exit.set()

        proc = await func(*args, **kwargs)

        exit_task = asyncio.create_task(wait_for_exit())
        tasks.add(exit_task)
        exit_task.add_done_callback(tasks.discard)

        wait_task = asyncio.create_task(wait_for_finish())
        tasks.add(wait_task)
        wait_task.add_done_callback(tasks.discard)
        wait_task.add_done_callback(lambda t: remove_signal_handler(shutdown))

        return proc

    return wrapper


@ensure_process_terminated
async def create_process(
    *args: Union[str, bytes, "os.PathLike[str]", "os.PathLike[bytes]"],
    cwd: Optional[Path] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0,
    )


@ensure_process_terminated
async def create_process_shell(
    command: Union[str, bytes],
    cwd: Optional[Path] = None,
    stdin: Optional[Union[IO[Any], int]] = None,
    stdout: Optional[Union[IO[Any], int]] = None,
    stderr: Optional[Union[IO[Any], int]] = None,
) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_shell(
        command,
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0,
    )


async def terminate_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return

    context = shield_signals() if WINDOWS else nullcontext()

    with context:
        if WINDOWS:
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()

        await process.wait()
