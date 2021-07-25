from typing import List, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.filters import is_done
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer

from . import BasePrompt, NoAnswer, Choice


class ListPrompt(BasePrompt[Choice]):

    def __init__(self,
                 question: str,
                 choices: List[Choice],
                 max_height: Optional[int] = None):
        self.question: str = question
        self.choices: List[Choice] = choices
        self._index: int = 0
        self._selected: List[Choice] = []
        self._answered: bool = False
        self._max_height: Optional[int] = max_height

    def _build_layout(self) -> Layout:
        layout = Layout(
            HSplit([
                Window(FormattedTextControl(self._get_prompt),
                       height=Dimension(1),
                       dont_extend_height=True),
                ConditionalContainer(
                    Window(FormattedTextControl(self._get_choices_prompt),
                           height=Dimension(1),
                           dont_extend_height=True), ~is_done)
            ]))
        return layout

    def _build_style(self, style: Style) -> Style:
        default = Style([("question", "bold"), ("answer", "fg:#FF9D00"),
                         ("annotation", "fg:#7F8C8D"),
                         ("selected", "fg:ansigreen noreverse")])
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up", eager=True)
        def previous(event: KeyPressEvent):
            self._index = (self._index - 1) % len(self.choices)

        @kb.add("down", eager=True)
        def next(event: KeyPressEvent):
            self._index = (self._index + 1) % len(self.choices)

        @kb.add("space", eager=True)
        def select(event: KeyPressEvent):
            choice = self.choices[self._index]
            if choice in self._selected:
                self._selected.remove(choice)
            else:
                self._selected.append(choice)

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._answered = True
            event.app.exit(result=self._selected)

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            event.app.exit(result=NoAnswer)

        return kb

    def _get_prompt(self) -> AnyFormattedText:
        prompts: AnyFormattedText = [("class:question", self.question.strip()),
                                     ("", " ")]
        if self._answered:
            prompts.append(
                ("class:answer", self.choices[self._index].name.strip()))
        else:
            prompts.append(
                ("class:annotation",
                 "(Use ↑ and ↓ to choose, Space to select, Enter to submit)"))
        return prompts

    def _get_choices_prompt(self) -> AnyFormattedText:
        prompts: AnyFormattedText = []
        for index, choice in enumerate(self.choices):
            if index == self._index:
                prompts.append(("class:selected", choice.name.strip() + "\n"))
            else:
                prompts.append(("class:unselected", choice.name.strip() + "\n"))
        return prompts
