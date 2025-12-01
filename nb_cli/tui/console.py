import locale
import signal
from typing import Final
from asyncio.subprocess import Process

import rich
import rich.text
from textual.reactive import var
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Log, Footer, Header

from nb_cli import _
from nb_cli.consts import WINDOWS
from nb_cli.handlers.process import terminate_process

SYS_ENCODING = locale.getpreferredencoding()


class LogConsole(ModalScreen):
    BINDINGS: Final = [
        ("escape,q,ctrl+c", "pop_screen", _("Close")),
        ("ctrl+l", "clear_output", _("Clear output")),
        ("ctrl+c", "cancel_proc", _("Cancel process")),
        ("ctrl+k", "terminate_proc", _("Terminate process")),
        ("ctrl+n", "copy", _("Copy content")),
    ]
    SUB_TITLE = _("Console output")

    _ACTION_CHECK: Final = {
        "pop_screen": False,
        "cancel_proc": True,
        "terminate_proc": True,
    }

    attached: var[bool] = var(False, bindings=True)
    _attached_proc: Process

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Log()

    async def attach_process(self, proc: Process):
        if proc.stdout is None:
            raise ValueError("The process has no stdout to read.")
        self._attached_proc = proc
        self.attached = True
        if proc.stderr is not None:
            self.notify(
                "[WARN] A process does not merge stderr into stdout,"
                "output may be incomplete."
            )

        log = self.query_one(Log)

        async for line in proc.stdout:
            log.write(line.decode(encoding=SYS_ENCODING, errors="replace"))

        if code := await proc.wait():
            log.write_line(
                "\n"
                + _(
                    "Process exited (code: {code}). Press ESC / q / Ctrl+C to close."
                ).format(code=code)
            )
        self.attached = False
        del self._attached_proc
        return proc

    async def action_pop_screen(self):
        if not self.attached:
            await self.app.pop_screen()
            return
        self.notify(
            _("Cannot leave current console until the process is done or terminated.")
        )

    async def action_cancel_proc(self):
        if not self.attached:
            return
        self._attached_proc.send_signal(
            signal.CTRL_C_EVENT if WINDOWS else signal.SIGINT
        )

    async def action_terminate_proc(self):
        if not self.attached:
            return
        await terminate_process(self._attached_proc)

    async def action_clear_output(self):
        log = self.query_one(Log)
        log.clear()

    async def action_copy(self):
        log = self.query_one(Log)
        # works on terminals that supports OSC 52.
        self.app.copy_to_clipboard(
            "\n".join(rich.text.Text.from_ansi(line).plain for line in log.lines)
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        return (
            self._ACTION_CHECK.get(action, True)
            if self.attached
            else not self._ACTION_CHECK.get(action, False)
        )
