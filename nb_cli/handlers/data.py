import os
import sys
from pathlib import Path
from typing import Literal

WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")


# -- Windows support functions --
def _get_win_folder_from_registry(
    csidl_name: Literal["CSIDL_APPDATA", "CSIDL_COMMON_APPDATA", "CSIDL_LOCAL_APPDATA"]
) -> Path:
    """
    This is a fallback technique at best. I'm not sure if using the
    registry for this guarantees us the correct answer for all CSIDL_*
    names.
    """
    import winreg

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    )
    directory, _type = winreg.QueryValueEx(key, shell_folder_name)
    return Path(directory)


def _get_win_folder_with_ctypes(
    csidl_name: Literal["CSIDL_APPDATA", "CSIDL_COMMON_APPDATA", "CSIDL_LOCAL_APPDATA"]
) -> Path:
    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = any(ord(c) > 255 for c in buf)
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return Path(buf.value)


if WINDOWS:
    try:
        import ctypes

        _get_win_folder = _get_win_folder_with_ctypes
    except ImportError:
        _get_win_folder = _get_win_folder_from_registry

    CACHE_DIR = _get_win_folder("CSIDL_LOCAL_APPDATA") / "nb-cli" / "Cache"
    DATA_DIR = _get_win_folder("CSIDL_LOCAL_APPDATA") / "nb-cli"
    CONFIG_DIR = DATA_DIR

elif sys.platform == "darwin":
    CACHE_DIR = Path("~/Library/Caches/nb-cli").expanduser()
    DATA_DIR = Path("~/Library/Application Support/nb-cli").expanduser()
    CONFIG_DIR = DATA_DIR

else:
    CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", "~/.cache")).expanduser() / "nb-cli"
    DATA_DIR = (
        Path(os.getenv("XDG_DATA_HOME", "~/.local/share")).expanduser() / "nb-cli"
    )
    CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser() / "nb-cli"
