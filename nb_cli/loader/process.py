import os
import signal
import platform
import subprocess
from typing import Dict, Optional

from nb_cli.utils import gen_script
from nb_cli.config import LocalConfig


class NoneBotProcess:
    process: Optional[subprocess.Popen] = None

    def __init__(
        self,
        config: LocalConfig,
        file: Optional[str] = None,
    ):
        self.config = config
        self.file: Optional[str] = file

    def _process_executor(self) -> int:
        self.process = subprocess.Popen(
            ["python", "-W", "ignore", "-"],
            stdin=subprocess.PIPE,
            encoding="utf-8",
        )
        ProcessManager.add(self)
        if self.process.stdin:
            if self.config.get("reload"):
                self.process.stdin.write(
                    gen_script(
                        self.config.get_adapters(),
                        self.config.get_builtin_plugins(),
                    )
                )
                self.process.stdin.close()
            else:
                self.process.communicate(
                    input=gen_script(
                        self.config.get_adapters(),
                        self.config.get_builtin_plugins(),
                    )
                )

        return self.process.returncode

    def _process_file_executor(self):
        if self.file is not None:
            self.process = subprocess.Popen(
                ["python", self.file],
                stdin=subprocess.PIPE,
                encoding="utf-8",
            )
            ProcessManager.add(self)
            return self.process.returncode

    def run(self):
        self._process_file_executor()
        self._process_executor()

    def terminate(self):
        if self.process is not None:
            pid = self.process.pid
            if platform.system() == "Windows":
                os.kill(pid, signal.CTRL_C_EVENT)
                self.process.wait()
            else:
                self.process.terminate()

            ProcessManager.remove(pid)


class ProcessManager:
    _processes: Dict[int, NoneBotProcess] = {}

    @classmethod
    def add(cls, process: NoneBotProcess):
        if process.process is not None:
            cls._processes[process.process.pid] = process

    @classmethod
    def remove(cls, pid: int):
        cls._processes.pop(pid)
