import signal
import asyncio
import threading
from types import FrameType
from typing import List, Callable, Optional

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

handlers: List[Callable[[int, Optional[FrameType]], None]] = []


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
    for handler in handlers:
        handler(signum, frame)


def register_signal_handler(
    handler: Callable[[int, Optional[FrameType]], None]
) -> None:
    handlers.append(handler)


def remove_signal_handler(handler: Callable[[int, Optional[FrameType]], None]) -> None:
    handlers.remove(handler)
