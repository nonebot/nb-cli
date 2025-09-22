from typing import Union, Generic, TypeVar, Optional

from textual import markup
from textual.widgets import Static
from textual.reactive import reactive

from nb_cli import _
from nb_cli.cli.utils import cut_text
from nb_cli.config.model import Tag, Driver, Plugin, Adapter

CARD_WIDTH = 49
CARD_HEIGHT = 6

_test_valid_style_mapping: dict[Optional[bool], str] = {
    None: "blue",
    True: "green",
    False: "red",
}
_test_valid_state_names: dict[Optional[bool], str] = {
    None: _("Unknown"),
    True: _("Passed"),
    False: _("Failed"),
}
_test_valid_state_skipped = _("Skipped")

T_module = TypeVar("T_module", Adapter, Driver, Plugin)


def _create_tag(*tags: Tag) -> str:
    return " ".join(
        f"[auto on {tag.color}]{markup.escape(tag.label)}[/]" for tag in tags
    )


def _create_status_bar(data: Union[Adapter, Driver, Plugin]) -> str:
    buf: list[str] = []
    if data.is_official:
        buf.append("[green]✦[/]")
    if isinstance(data, Plugin):
        color = "gray" if data.skip_test else _test_valid_style_mapping[data.valid]
        buf.append(f"[{color}]●[/]")
    return " ".join(buf)


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
    data: reactive[Optional[T_module]] = reactive(None, init=False)

    def render(self):
        desc = (
            cut_text(self.data.desc, max(self.size.width, 45), 2) if self.data else ""
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
            self.border_title = self.data.name
            self.border_subtitle = _create_status_bar(self.data)

        return content

    def on_click(self) -> None:
        pass
