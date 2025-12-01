import os
import asyncio
from typing import Final, Generic, TypeVar

import textual
from textual import markup
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Grid, Vertical, Horizontal, VerticalScroll

from nb_cli import _
from nb_cli.cli.utils import cut_text
from nb_cli.config import GLOBAL_CONFIG
from nb_cli.tui.console import LogConsole
from nb_cli.handlers.pip import call_pip_install
from nb_cli.config.model import Tag, Driver, Plugin, Adapter

CARD_WIDTH = 49
CARD_HEIGHT = 6

_test_valid_style_mapping: dict[bool | None, str] = {
    None: "blue",
    True: "green",
    False: "red",
}
_test_valid_state_names: dict[bool | None, str] = {
    None: _("Unknown state"),
    True: _("Plugin test passed"),
    False: _("Plugin test failed"),
}
_test_valid_state_skipped = _("Plugin test skipped")

T_module = TypeVar("T_module", Adapter, Driver, Plugin)


def _create_tag(*tags: Tag) -> str:
    return " ".join(
        f"[auto on {tag.color}]{markup.escape(tag.label.strip())}[/]" for tag in tags
    )


def _create_status_bar(data: Adapter | Driver | Plugin) -> str:
    buf: list[str] = []
    if data.is_official:
        buf.append("[green]✦[/]")
    if isinstance(data, Plugin):
        color = "gray" if data.skip_test else _test_valid_style_mapping[data.valid]
        buf.append(f"[{color}]●[/]")
    return " ".join(buf)


def _create_valid_state(data: Adapter | Driver | Plugin) -> str:
    if not isinstance(data, Plugin):
        return ""
    if data.skip_test:
        return f"[auto on aqua]{_test_valid_state_skipped}[/]"
    return (
        f"[auto on {_test_valid_style_mapping[data.valid]}]"
        f"{_test_valid_state_names[data.valid]}[/]"
    )


class CardPopup(ModalScreen, Generic[T_module]):
    BINDINGS: Final = [
        ("esc,q,ctrl+c", "app.pop_screen"),
        ("ctrl+z", "toggle_dark", _("Toggle dark mode")),
    ]
    CSS = """
    CardPopup {
        align: center middle;
    }

    #card-content {
        width: 70%;
        height: 70%;
        background: $surface;
        grid-size: 3 3;
        padding: 0 1;

        #top {
            column-span: 3;
            padding: 1 2;
            align-vertical: middle;
            border-bottom: solid #ea5252;

            Grid {
                align-vertical: middle;
            }
        }

        #content {
            row-span: 2;
            column-span: 2;
            padding: 1 2;
        }

        #info {
            row-span: 2;
            padding: 1 2;
            background: $surface;
        }
    }

    #card-content.-dark {
        border: round #e0e0e0;
    }

    #card-content.-light {
        border: round #101010;
    }

    #top > Grid {
        grid-size: 1 2;
    }

    #gap {
        width: 1fr;
    }

    #top > Vertical {
        padding: 1 2;
        align: right middle;
    }

    #content {
        #content-desc {
            height: 1fr;
        }

        #content-tags {
            height: 2;
        }
    }
    """
    data: reactive[T_module | None] = reactive(None, init=False, recompose=True)

    def compose(self) -> ComposeResult:
        with Grid(id="card-content", classes="-dark"):
            with Horizontal(id="top"):
                with Grid():
                    yield Static(
                        (
                            markup.escape(self.data.name.strip())
                            + "    "
                            + _create_valid_state(self.data)
                        )
                        if self.data
                        else ""
                    )
                    yield Static(
                        markup.escape(
                            _("Author: {author}").format(author=self.data.author)
                        )
                        if self.data
                        else ""
                    )
                yield Static(id="gap")
                with Vertical():
                    yield Button(_("Install"), id="install-module")
            with Vertical(id="content"):
                yield Static(
                    markup.escape(self.data.desc.strip()) if self.data else "",
                    id="content-desc",
                )
                yield Static(
                    _create_tag(*self.data.tags) if self.data else "", id="content-tags"
                )
            with VerticalScroll(id="info"):
                version, package_name, module_name, time, homepage = "", "", "", "", ""
                if self.data:
                    version = (
                        _("Latest version:")
                        + f"\n  [b]{markup.escape(self.data.version)}[/]"
                    )
                    package_name = (
                        _("Package name:") + f"\n  [b]{self.data.project_link}[/]"
                    )
                    module_name = (
                        _("Module name:") + f"\n  [b]{self.data.module_name}[/]"
                    )
                    time = _("Recent update:") + "\n  [b]{time}[/]".format(
                        time=self.data.time.strftime("%Y/%m/%d %H:%M:%S")
                    )
                    _fix_homepage = (
                        f"https://nonebot.dev{self.data.homepage}"
                        if self.data.homepage.startswith("/")
                        else self.data.homepage
                    )
                    homepage = "[link='{homepage}'][b]> {text}[/b][/]".format(
                        homepage=_fix_homepage, text=_("Homepage")
                    )
                yield Static(
                    f"{version}\n{package_name}\n{module_name}\n{time}\n\n{homepage}\n"
                )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.app.theme, style = (
            ("textual-dark", "-dark")
            if self.app.theme == "textual-light"
            else ("textual-light", "-light")
        )
        c = self.query_one("#card-content", Grid)
        c.remove_class("-dark", "-light", update=False)
        c.add_class(style)

    @textual.on(Button.Pressed, "#install-module")
    async def handle_install_module(self):
        if self.data is None:
            return
        await self.app.push_screen("console")
        con = self.app.get_screen("console", LogConsole)
        proc = await call_pip_install(
            self.data.as_dependency(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy() | {"FORCE_COLOR": "1"},
        )
        await con.attach_process(proc)
        if proc.returncode == 0:
            GLOBAL_CONFIG.add_dependency(self.data)
            if isinstance(self.data, Adapter):
                GLOBAL_CONFIG.add_adapter(self.data)
            elif isinstance(self.data, Plugin):
                GLOBAL_CONFIG.add_plugin(self.data)
            await self.app.pop_screen()
            self.notify(
                _('Successfully installed "{name}".').format(name=self.data.name)
            )


class Card(Static, Generic[T_module]):
    DEFAULT_CSS = """
    Card {
        background: $surface;
        margin: 0 1;
        padding: 0 2;
        height: 6;
    }

    Card.-dark {
        border: round #e0e0e0;
    }

    Card.-light {
        border: round #101010;
    }

    Card:hover {
        border: round #ea5252;
    }
    """
    data: reactive[T_module | None] = reactive(None, init=False)

    def render(self):
        desc = (
            cut_text(self.data.desc.strip(), max(self.size.width, 40), 2)
            if self.data
            else ""
        )
        content = ("[$text]{desc}[/]\n" "{tags}\n" "[gray]{author}[/]").format(
            desc=(_("Initializing...") if self.data is None else markup.escape(desc)),
            tags="" if self.data is None else _create_tag(*self.data.tags),
            author=(
                ""
                if self.data is None
                else _("Author: {author}").format(
                    author=markup.escape(self.data.author)
                )
            ),
        )
        if self.data:
            self.border_title = self.data.name.strip()
            self.border_subtitle = _create_status_bar(self.data)

        return content

    def on_click(self) -> None:
        self.app.push_screen(
            CardPopup[T_module]().data_bind(
                data=Card[T_module].data  # pyright: ignore[reportGeneralTypeIssues]
            )
        )
