from functools import partial
from typing import Generic, TypeVar, ClassVar

from textual.timer import Timer
from textual.reactive import var
from textual.widget import Widget
from textual.app import App, ComposeResult
from textual.widgets import Input, Footer, Header
from textual.containers import ItemGrid, Vertical, VerticalScroll

from nb_cli import _
from nb_cli.tui.card import Card
from nb_cli.tui.console import LogConsole
from nb_cli.cli.utils import advanced_search_filter
from nb_cli.config.model import Driver, Plugin, Adapter

T_widget = TypeVar("T_widget", bound=Widget)
T_module = TypeVar("T_module", Adapter, Driver, Plugin)

SEARCH_DEBOUNCE_DELAY: float = 0.3


class Gallery(App, Generic[T_module]):
    BINDINGS: ClassVar = [
        ("escape,q,ctrl+c", "quit", _("Quit")),
        ("/", "toggle_search", _("Search")),
        ("ctrl+z", "toggle_dark", _("Toggle dark mode")),
        ("ctrl+n", "app.push_screen('console')", _("Open console")),
    ]
    SCREENS: ClassVar = {"console": LogConsole}

    CSS = """
    Footer, VerticalScroll, Input {
        background: $background;
        color: $text;
    }

    #modules {
        align: center middle;
    }

    #query-filter {
        height: 2;
        border: none;
        border-top: solid #ea5252;
    }
    """

    datasource: var[list[T_module]] = var(list, init=False)
    cards: var[list[Card[T_module]]] = var(list)
    query_open: var[bool] = var(False)
    query_filter: var[str] = var("", always_update=True)
    query_debounce: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical():
            with VerticalScroll():
                yield ItemGrid(id="modules", min_column_width=49)
            yield Input(id="query-filter", placeholder=_("Search..."))

    async def on_mount(self):
        input_ = self.query_one("#query-filter", Input)
        input_.display = self.query_open
        if input_.display:
            input_.focus()
        grid = self.query_one("#modules", ItemGrid)
        for p in self.datasource:
            c = Card[T_module](classes="-dark")
            self.cards.append(c)
            await grid.mount(c)
            c.data = p

    def action_toggle_search(self):
        self.query_open = not self.query_open

    def on_input_blurred(self, event: Input.Blurred):
        event.input.display = False

    def on_input_submitted(self, event: Input.Submitted):
        event.input.display = False

    def _update_query_filter(self, input_: str):
        self.query_filter = input_
        self.query_debounce = None

    def on_input_changed(self, event: Input.Changed):
        if self.query_debounce is not None:
            self.query_debounce.stop()
        self.query_debounce = self.set_timer(
            SEARCH_DEBOUNCE_DELAY, partial(self._update_query_filter, event.value)
        )

    def watch_query_open(self, _: bool, new_st: bool):
        input_ = self.query_one("#query-filter", Input)
        input_.display = new_st
        if input_.display:
            input_.focus()

    def watch_query_filter(self, _: str, new_qf: str):
        for x in self.cards:
            if x.data is None:
                x.display = False
                continue
            x.display = advanced_search_filter(new_qf, x.data)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme, style = (
            ("textual-dark", "-dark")
            if self.theme == "textual-light"
            else ("textual-light", "-light")
        )
        for c in self.cards:
            c.remove_class("-dark", "-light", update=False)
            c.add_class(style)
