"""
This script will install NoneBot CLI and its dependencies.

It does, in order:

  - Creates a virtual environment using venv (or virtualenv zipapp) in the correct OS data dir which will be
      - `%APPDATA%\\nonebot_cli` on Windows
      -  ~/Library/Application Support/nonebot_cli on MacOS
      - `${XDG_DATA_HOME}/nonebot_cli` (or `~/.local/share/nonebot_cli` if it's not set) on UNIX systems
      - In `${NONEBOT_CLI_HOME}` if it's set.
  - Installs the latest or given version of NoneBot CLI inside this virtual environment.
  - Installs a `nb` script in the Python user directory (or `${NONEBOT_CLI_HOME/bin}` if `NONEBOT_CLI_HOME` is set).
  - On failure, the error log is written to nonebot-cli-installer-error-*.log and any previously existing environment
    is restored.
"""

import os
import re
import sys
import json
import site
import shutil
import argparse
import tempfile
import sysconfig
import subprocess
from pathlib import Path
from functools import cmp_to_key
from io import UnsupportedOperation
from typing import Iterator, Optional
from urllib.request import Request, urlopen
from contextlib import closing, contextmanager

SHELL = os.getenv("SHELL", "")
WINDOWS = sys.platform.startswith("win") or (
    sys.platform == "cli" and os.name == "nt"
)
MINGW = sysconfig.get_platform().startswith("mingw")
MACOS = sys.platform == "darwin"

FOREGROUND_COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
}

BACKGROUND_COLORS = {
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
}

OPTIONS = {"bold": 1, "underscore": 4, "blink": 5, "reverse": 7, "conceal": 8}


def style(fg, bg, options):
    codes = []

    if fg:
        codes.append(FOREGROUND_COLORS[fg])

    if bg:
        codes.append(BACKGROUND_COLORS[bg])

    if options:
        if not isinstance(options, (list, tuple)):
            options = [options]

        for option in options:
            codes.append(OPTIONS[option])

    return "\033[{}m".format(";".join(map(str, codes)))


STYLES = {
    "info": style("cyan", None, None),
    "comment": style("yellow", None, None),
    "success": style("green", None, None),
    "error": style("red", None, None),
    "warning": style("yellow", None, None),
    "b": style(None, None, ("bold",)),
}


def is_decorated():
    if WINDOWS:
        return (
            os.getenv("ANSICON") is not None
            or "ON" == os.getenv("ConEmuANSI")
            or "xterm" == os.getenv("Term")
        )

    if not hasattr(sys.stdout, "fileno"):
        return False

    try:
        return os.isatty(sys.stdout.fileno())
    except UnsupportedOperation:
        return False


def is_interactive():
    if not hasattr(sys.stdin, "fileno"):
        return False

    try:
        return os.isatty(sys.stdin.fileno())
    except UnsupportedOperation:
        return False


def colorize(style, text):
    if not is_decorated():
        return text

    return "{}{}\033[0m".format(STYLES[style], text)


def string_to_bool(value):
    value = value.lower()

    return value in {"true", "1", "y", "yes"}


def data_dir(version: Optional[str] = None) -> Path:
    home = os.getenv("NONEBOT_CLI_HOME")
    if home:
        return Path(home).expanduser()

    if WINDOWS:
        const = "CSIDL_APPDATA"
        path = os.path.normpath(_get_win_folder(const))
        path = os.path.join(path, "nonebot_cli")
    elif MACOS:
        path = os.path.expanduser("~/Library/Application Support/nonebot_cli")
    else:
        path = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        path = os.path.join(path, "nonebot_cli")

    if version:
        path = os.path.join(path, version)

    return Path(path)


def bin_dir(version: Optional[str] = None) -> Path:
    home = os.getenv("NONEBOT_CLI_HOME")

    if home:
        return Path(home, "bin").expanduser()

    user_base = site.getuserbase()

    if WINDOWS and not MINGW:
        bin_dir = os.path.join(user_base, "Scripts")
    else:
        bin_dir = os.path.join(user_base, "bin")

    return Path(bin_dir)


def _get_win_folder_from_registry(csidl_name):
    import winreg as _winreg

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]

    key = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    )
    dir, type = _winreg.QueryValueEx(key, shell_folder_name)

    return dir


def _get_win_folder_with_ctypes(csidl_name):
    import ctypes

    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return buf.value


if WINDOWS:
    try:
        from ctypes import windll  # noqa: F401

        _get_win_folder = _get_win_folder_with_ctypes
    except ImportError:
        _get_win_folder = _get_win_folder_from_registry


PRE_MESSAGE = """# Welcome to {cli}!

This will download and install the latest version of {cli},
a helper for running NoneBot 2.

It will add the `nb` command to {cli}'s bin directory, located at:

{cli_home_bin}

You can uninstall at any time by executing this script with the --uninstall option,
and these changes will be reverted.
"""

POST_MESSAGE = """{cli} ({version}) is installed now. Great!

You can test that everything is set up by executing:

`{test_command}`
"""

POST_MESSAGE_NOT_IN_PATH = """{cli} ({version}) is installed now. Great!

To get started you need {cli}'s bin directory ({cli_home_bin}) in your `PATH`
environment variable.
{configure_message}
Alternatively, you can call {cli} explicitly with `{cli_executable}`.

You can test that everything is set up by executing:

`{test_command}`
"""

POST_MESSAGE_CONFIGURE_UNIX = """
Add `export PATH="{cli_home_bin}:$PATH"` to your shell configuration file.
"""

POST_MESSAGE_CONFIGURE_FISH = """
You can execute `set -U fish_user_paths {cli_home_bin} $fish_user_paths`
"""

POST_MESSAGE_CONFIGURE_WINDOWS = """"""


class InstallationError(RuntimeError):
    def __init__(self, return_code: int = 0, log: Optional[str] = None):
        super(InstallationError, self).__init__()
        self.return_code = return_code
        self.log = log


class VirtualEnvironment:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._bin_path = self._path.joinpath(
            "Scripts" if WINDOWS and not MINGW else "bin"
        )
        # str is required for compatibility with subprocess run on CPython <= 3.7 on Windows
        self._python = str(
            self._path.joinpath(
                self._bin_path, "python.exe" if WINDOWS else "python"
            )
        )

    @property
    def path(self):
        return self._path

    @property
    def bin_path(self):
        return self._bin_path

    @classmethod
    def make(cls, target: Path) -> "VirtualEnvironment":
        try:
            import venv

            builder = venv.EnvBuilder(clear=True, with_pip=True, symlinks=False)
            context = builder.ensure_directories(target)

            if (
                WINDOWS
                and hasattr(context, "env_exec_cmd")
                and context.env_exe != context.env_exec_cmd
            ):
                target = target.resolve()

            builder.create(target)
        except ImportError:
            # fallback to using virtualenv package if venv is not available, eg: ubuntu
            python_version = (
                f"{sys.version_info.major}.{sys.version_info.minor}"
            )
            virtualenv_bootstrap_url = f"https://bootstrap.pypa.io/virtualenv/{python_version}/virtualenv.pyz"

            with tempfile.TemporaryDirectory(
                prefix="nonebot-cli-installer"
            ) as temp_dir:
                virtualenv_pyz = Path(temp_dir) / "virtualenv.pyz"
                request = Request(
                    virtualenv_bootstrap_url,
                    headers={"User-Agent": "Python NoneBot CLI"},
                )
                virtualenv_pyz.write_bytes(urlopen(request).read())
                cls.run(
                    sys.executable,
                    virtualenv_pyz,
                    "--clear",
                    "--always-copy",
                    target,
                )

        # We add a special file so that NoneBot CLI can detect
        # its own virtual environment
        target.joinpath("nonebot_cli_env").touch()

        env = cls(target)

        # we do this here to ensure that outdated system default pip does not trigger older bugs
        env.pip("install", "--disable-pip-version-check", "--upgrade", "pip")

        return env

    @staticmethod
    def run(*args, **kwargs) -> subprocess.CompletedProcess:
        completed_process = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs,
        )
        if completed_process.returncode != 0:
            raise InstallationError(
                return_code=completed_process.returncode,
                log=completed_process.stdout.decode(),
            )
        return completed_process

    def python(self, *args, **kwargs) -> subprocess.CompletedProcess:
        return self.run(self._python, *args, **kwargs)

    def pip(self, *args, **kwargs) -> subprocess.CompletedProcess:
        return self.python("-m", "pip", *args, **kwargs)


class Cursor:
    def __init__(self) -> None:
        self._output = sys.stdout

    def move_up(self, lines: int = 1) -> "Cursor":
        self._output.write("\x1b[{}A".format(lines))

        return self

    def move_down(self, lines: int = 1) -> "Cursor":
        self._output.write("\x1b[{}B".format(lines))

        return self

    def move_right(self, columns: int = 1) -> "Cursor":
        self._output.write("\x1b[{}C".format(columns))

        return self

    def move_left(self, columns: int = 1) -> "Cursor":
        self._output.write("\x1b[{}D".format(columns))

        return self

    def move_to_column(self, column: int) -> "Cursor":
        self._output.write("\x1b[{}G".format(column))

        return self

    def move_to_position(self, column: int, row: int) -> "Cursor":
        self._output.write("\x1b[{};{}H".format(row + 1, column))

        return self

    def save_position(self) -> "Cursor":
        self._output.write("\x1b7")

        return self

    def restore_position(self) -> "Cursor":
        self._output.write("\x1b8")

        return self

    def hide(self) -> "Cursor":
        self._output.write("\x1b[?25l")

        return self

    def show(self) -> "Cursor":
        self._output.write("\x1b[?25h\x1b[?0c")

        return self

    def clear_line(self) -> "Cursor":
        """
        Clears all the output from the current line.
        """
        self._output.write("\x1b[2K")

        return self

    def clear_line_after(self) -> "Cursor":
        """
        Clears all the output from the current line after the current position.
        """
        self._output.write("\x1b[K")

        return self

    def clear_output(self) -> "Cursor":
        """
        Clears all the output from the cursors' current position
        to the end of the screen.
        """
        self._output.write("\x1b[0J")

        return self

    def clear_screen(self) -> "Cursor":
        """
        Clears the entire screen.
        """
        self._output.write("\x1b[2J")

        return self


class Installer:
    METADATA_URL = "https://pypi.org/pypi/nb-cli/json"
    VERSION_REGEX = re.compile(
        r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?"
        "("
        "[._-]?"
        r"(?:(stable|beta|b|rc|RC|alpha|a|patch|pl|p)((?:[.-]?\d+)*)?)?"
        "([.-]?dev)?"
        ")?"
        r"(?:\+[^\s]+)?"
    )

    def __init__(
        self,
        version: Optional[str] = None,
        preview: bool = False,
        force: bool = False,
        accept_all: bool = False,
        git: Optional[str] = None,
        path: Optional[str] = None,
    ) -> None:
        self._version = version
        self._preview = preview
        self._force = force
        self._accept_all = accept_all
        self._git = git
        self._path = path
        self._data_dir = data_dir()
        self._bin_dir = bin_dir()
        self._cursor = Cursor()

    def allows_prereleases(self) -> bool:
        return self._preview

    def run(self) -> int:
        if self._git:
            version = self._git
        elif self._path:
            version = self._path
        else:
            try:
                version, current_version = self.get_version()
            except ValueError:
                return 1

        if version is None:
            return 0

        self.display_pre_message()
        self.ensure_directories()

        def _is_self_upgrade_supported(x):
            mx = self.VERSION_REGEX.match(x)

            if mx is None:
                # the version is not semver, perhaps scm or file, we assume upgrade is supported
                return True

            vx = tuple(int(p) for p in mx.groups()[:3]) + (mx.group(5),)
            return vx >= (1, 1, 7)

        if version and not _is_self_upgrade_supported(version):
            self._write(
                colorize(
                    "warning",
                    f"You are installing {version}. When using the current installer, this version does not support "
                    f"updating using the 'self update' command. Please use 1.0 or later.",
                )
            )
            if not self._accept_all:
                continue_install = (
                    input("Do you want to continue? ([y]/n) ") or "y"
                )
                if continue_install.lower() in {"n", "no"}:
                    return 0

        try:
            self.install(version)
        except subprocess.CalledProcessError as e:
            raise InstallationError(
                return_code=e.returncode, log=e.output.decode()
            )

        self._write("")
        self.display_post_message(version)

        return 0

    def install(self, version, upgrade=False):
        """
        Installs NoneBot CLI in $NONEBOT_CLI_HOME.
        """
        self._write(
            "Installing {} ({})".format(
                colorize("info", "NoneBot CLI"), colorize("info", version)
            )
        )

        with self.make_env(version) as env:
            self.install_cli(version, env)
            self.make_bin(version, env)
            self._data_dir.joinpath("VERSION").write_text(version)
            self._install_comment(version, "Done")

            return 0

    def uninstall(self) -> int:
        if not self._data_dir.exists():
            self._write(
                "{} is not currently installed.".format(
                    colorize("info", "NoneBot CLI")
                )
            )

            return 1

        version = None
        if self._data_dir.joinpath("VERSION").exists():
            version = self._data_dir.joinpath("VERSION").read_text().strip()

        if version:
            self._write(
                "Removing {} ({})".format(
                    colorize("info", "NoneBot CLI"), colorize("b", version)
                )
            )
        else:
            self._write("Removing {}".format(colorize("info", "NoneBot CLI")))

        shutil.rmtree(str(self._data_dir))
        for script in ["nb", "nb.bat", "nb.exe"]:
            if self._bin_dir.joinpath(script).exists():
                self._bin_dir.joinpath(script).unlink()

        return 0

    def _install_comment(self, version: str, message: str):
        self._overwrite(
            "Installing {} ({}): {}".format(
                colorize("info", "NoneBot CLI"),
                colorize("b", version),
                colorize("comment", message),
            )
        )

    @contextmanager
    def make_env(self, version: str) -> Iterator[VirtualEnvironment]:
        env_path = self._data_dir.joinpath("venv")
        env_path_saved = env_path.with_suffix(".save")

        if env_path.exists():
            self._install_comment(version, "Saving existing environment")
            if env_path_saved.exists():
                shutil.rmtree(env_path_saved)
            shutil.move(env_path, env_path_saved)

        try:
            self._install_comment(version, "Creating environment")
            yield VirtualEnvironment.make(env_path)
        except Exception as e:
            if env_path.exists():
                self._install_comment(
                    version, "An error occurred. Removing partial environment."
                )
                shutil.rmtree(env_path)

            if env_path_saved.exists():
                self._install_comment(
                    version, "Restoring previously saved environment."
                )
                shutil.move(env_path_saved, env_path)

            raise e
        else:
            if env_path_saved.exists():
                shutil.rmtree(env_path_saved, ignore_errors=True)

    def make_bin(self, version: str, env: VirtualEnvironment) -> None:
        self._install_comment(version, "Creating script")
        self._bin_dir.mkdir(parents=True, exist_ok=True)

        script = "nb.exe" if WINDOWS else "nb"
        target_script = env.bin_path.joinpath(script)

        if self._bin_dir.joinpath(script).exists():
            self._bin_dir.joinpath(script).unlink()

        try:
            self._bin_dir.joinpath(script).symlink_to(target_script)
        except OSError:
            # This can happen if the user
            # does not have the correct permission on Windows
            shutil.copy(target_script, self._bin_dir.joinpath(script))

    def install_cli(self, version: str, env: VirtualEnvironment) -> None:
        self._install_comment(version, "Installing NoneBot CLI")

        if self._git:
            specification = "git+" + version
        elif self._path:
            specification = version
        else:
            specification = f"nb-cli=={version}"

        env.pip("install", specification)

    def display_pre_message(self) -> None:
        kwargs = {
            "cli": colorize("info", "NoneBot CLI"),
            "cli_home_bin": colorize("comment", self._bin_dir),
        }
        self._write(PRE_MESSAGE.format(**kwargs))

    def display_post_message(self, version: str) -> None:
        if WINDOWS:
            return self.display_post_message_windows(version)

        if SHELL == "fish":
            return self.display_post_message_fish(version)

        return self.display_post_message_unix(version)

    def display_post_message_windows(self, version: str) -> None:
        path = self.get_windows_path_var()

        message = POST_MESSAGE_NOT_IN_PATH
        if path and str(self._bin_dir) in path:
            message = POST_MESSAGE

        self._write(
            message.format(
                cli=colorize("info", "NoneBot CLI"),
                version=colorize("b", version),
                cli_home_bin=colorize("comment", self._bin_dir),
                cli_executable=colorize("b", self._bin_dir.joinpath("nb")),
                configure_message=POST_MESSAGE_CONFIGURE_WINDOWS.format(
                    cli_home_bin=colorize("comment", self._bin_dir)
                ),
                test_command=colorize("b", "nb --version"),
            )
        )

    def get_windows_path_var(self) -> Optional[str]:
        import winreg

        with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as root:
            with winreg.OpenKey(
                root, "Environment", 0, winreg.KEY_ALL_ACCESS
            ) as key:
                path, _ = winreg.QueryValueEx(key, "PATH")

                return path

    def display_post_message_fish(self, version: str) -> None:
        fish_user_paths = subprocess.check_output(
            ["fish", "-c", "echo $fish_user_paths"]
        ).decode("utf-8")

        message = POST_MESSAGE_NOT_IN_PATH
        if fish_user_paths and str(self._bin_dir) in fish_user_paths:
            message = POST_MESSAGE

        self._write(
            message.format(
                cli=colorize("info", "NoneBot CLI"),
                version=colorize("b", version),
                cli_home_bin=colorize("comment", self._bin_dir),
                cli_executable=colorize("b", self._bin_dir.joinpath("nb")),
                configure_message=POST_MESSAGE_CONFIGURE_FISH.format(
                    cli_home_bin=colorize("comment", self._bin_dir)
                ),
                test_command=colorize("b", "nb --version"),
            )
        )

    def display_post_message_unix(self, version: str) -> None:
        paths = os.getenv("PATH", "").split(":")

        message = POST_MESSAGE_NOT_IN_PATH
        if paths and str(self._bin_dir) in paths:
            message = POST_MESSAGE

        self._write(
            message.format(
                cli=colorize("info", "NoneBot CLI"),
                version=colorize("b", version),
                cli_home_bin=colorize("comment", self._bin_dir),
                cli_executable=colorize("b", self._bin_dir.joinpath("nb")),
                configure_message=POST_MESSAGE_CONFIGURE_UNIX.format(
                    cli_home_bin=colorize("comment", self._bin_dir)
                ),
                test_command=colorize("b", "nb --version"),
            )
        )

    def ensure_directories(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._bin_dir.mkdir(parents=True, exist_ok=True)

    def get_version(self):
        current_version = None
        if self._data_dir.joinpath("VERSION").exists():
            current_version = (
                self._data_dir.joinpath("VERSION").read_text().strip()
            )

        self._write(colorize("info", "Retrieving NoneBot CLI metadata"))

        metadata = json.loads(self._get(self.METADATA_URL).decode())

        def _compare_versions(x, y):
            mx = self.VERSION_REGEX.match(x)
            my = self.VERSION_REGEX.match(y)

            vx = tuple(int(p) for p in mx.groups()[:3]) + (mx.group(5),)
            vy = tuple(int(p) for p in my.groups()[:3]) + (my.group(5),)

            if vx < vy:
                return -1
            elif vx > vy:
                return 1

            return 0

        self._write("")
        releases = sorted(
            metadata["releases"].keys(), key=cmp_to_key(_compare_versions)
        )

        if self._version and self._version not in releases:
            msg = "Version {} does not exist.".format(self._version)
            self._write(colorize("error", msg))

            raise ValueError(msg)

        version = self._version
        if not version:
            for release in reversed(releases):
                m = self.VERSION_REGEX.match(release)
                if m.group(5) and not self.allows_prereleases():
                    continue

                version = release

                break

        if current_version == version and not self._force:
            self._write(
                "The latest version ({}) is already installed.".format(
                    colorize("b", version)
                )
            )

            return None, current_version

        return version, current_version

    def _write(self, line) -> None:
        sys.stdout.write(line + "\n")

    def _overwrite(self, line) -> None:
        if not is_decorated():
            return self._write(line)

        self._cursor.move_up()
        self._cursor.clear_line()
        self._write(line)

    def _get(self, url):
        request = Request(url, headers={"User-Agent": "Python NoneBot CLI"})

        with closing(urlopen(request)) as r:
            return r.read()


def main():
    parser = argparse.ArgumentParser(
        description="Installs the latest (or given) version of NoneBot CLI"
    )
    parser.add_argument(
        "-p",
        "--preview",
        help="install preview version",
        dest="preview",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--version", help="install named version", dest="version"
    )
    parser.add_argument(
        "-f",
        "--force",
        help="install on top of existing version",
        dest="force",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-y",
        "--yes",
        help="accept all prompts",
        dest="accept_all",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--uninstall",
        help="uninstall nonebot cli",
        dest="uninstall",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--path",
        dest="path",
        action="store",
        help=(
            "Install from a given path (file or directory) instead of "
            "fetching the latest version of NoneBot CLI available online."
        ),
    )
    parser.add_argument(
        "--git",
        dest="git",
        action="store",
        help=(
            "Install from a git repository instead of fetching the latest version "
            "of NoneBot CLI available online."
        ),
    )

    args = parser.parse_args()

    installer = Installer(
        version=args.version or os.getenv("NONEBOT_CLI_VERSION"),
        preview=args.preview
        or string_to_bool(os.getenv("NONEBOT_CLI_PREVIEW", "0")),
        force=args.force,
        accept_all=args.accept_all
        or string_to_bool(os.getenv("NONEBOT_CLI_ACCEPT", "0"))
        or not is_interactive(),
        path=args.path,
        git=args.git,
    )

    if args.uninstall or string_to_bool(
        os.getenv("NONEBOT_CLI_UNINSTALL", "0")
    ):
        return installer.uninstall()

    try:
        return installer.run()
    except InstallationError as e:
        installer._write(colorize("error", "NoneBot CLI installation failed."))

        if e.log is not None:
            import traceback

            _, path = tempfile.mkstemp(
                suffix=".log",
                prefix="nonebot-cli-installer-error-",
                dir=str(Path.cwd()),
                text=True,
            )
            installer._write(colorize("error", f"See {path} for error logs."))
            text = f"{e.log}\nTraceback:\n\n{''.join(traceback.format_tb(e.__traceback__))}"
            Path(path).write_text(text)

        return e.return_code


if __name__ == "__main__":
    sys.exit(main())
