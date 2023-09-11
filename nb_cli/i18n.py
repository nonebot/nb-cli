import locale
import gettext
import contextlib
from pathlib import Path
from typing import Optional

from .consts import WINDOWS


def _get_win_locale_with_ctypes() -> Optional[str]:
    import ctypes  # noqa: F811

    kernel32 = ctypes.windll.kernel32
    lcid: int = kernel32.GetUserDefaultUILanguage()
    return locale.windows_locale.get(lcid)


def _get_win_locale_from_registry() -> Optional[str]:
    import winreg

    with contextlib.suppress(Exception):
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Control Panel\International"
        ) as key:
            if lcid := winreg.QueryValueEx(key, "Locale")[0]:
                return locale.windows_locale.get(int(lcid, 16))


if WINDOWS:
    try:
        import ctypes  # noqa: F401

        _get_win_locale = _get_win_locale_with_ctypes
    except ImportError:
        _get_win_locale = _get_win_locale_from_registry

    def get_locale() -> Optional[str]:
        return _get_win_locale()

else:

    def get_locale() -> Optional[str]:
        return locale.getlocale(locale.LC_MESSAGES)[0]


t = gettext.translation(
    "nb-cli",
    localedir=Path(__file__).parent / "locale",
    languages=[lang] if (lang := get_locale()) else None,
    fallback=True,
)
_ = t.gettext
