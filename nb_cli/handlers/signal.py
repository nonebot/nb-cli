import signal
import asyncio
import threading
from types import FrameType
from contextlib import contextmanager
from typing import List, Callable, Optional, Generator

from nb_cli.consts import WINDOWS

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
if WINDOWS:
    HANDLED_SIGNALS += (signal.SIGBREAK,)  # Windows signal 21. Sent by Ctrl+Break.

handlers: List[Callable[[int, Optional[FrameType]], None]] = []


class _ShieldContext:
    def __init__(self) -> None:
        self._counter = 0

    def acquire(self) -> None:
        self._counter += 1

    def release(self) -> None:
        self._counter -= 1

    def active(self) -> bool:
        return self._counter > 0


shield_context = _ShieldContext()


def install_signal_handler() -> None:
    if threading.current_thread() is not threading.main_thread():
        # Signals can only be listened to from the main thread.
        return

    loop = asyncio.get_event_loop()

    try:
        for sig in HANDLED_SIGNALS:
            loop.add_signal_handler(sig, handle_signal, sig, None)
    except NotImplementedError:
        # Windows
        for sig in HANDLED_SIGNALS:
            signal.signal(sig, handle_signal)


def handle_signal(signum: int, frame: Optional[FrameType]) -> None:
    if shield_context.active():
        return

    for handler in handlers:
        handler(signum, frame)


def register_signal_handler(
    handler: Callable[[int, Optional[FrameType]], None]
) -> None:
    handlers.append(handler)


def remove_signal_handler(handler: Callable[[int, Optional[FrameType]], None]) -> None:
    handlers.remove(handler)


@contextmanager
def shield_signals() -> Generator[None, None, None]:
    shield_context.acquire()
    try:
        yield
    finally:
        shield_context.release()
