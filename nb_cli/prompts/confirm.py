from typing import Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.application import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.validation import Validator
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

from . import NoAnswer, BasePrompt


class ConfirmPrompt(BasePrompt[bool]):
    """Simple Confirm Prompt.

    Style class guide:

    ```
    [?] Choose a choice and return? (Y/n)
    └┬┘ └──────────────┬──────────┘ └─┬─┘
    questionmark    question      annotation
    ```
    """

    def __init__(
        self,
        question: str,
        question_mark: str = "[?]",
        default_choice: Optional[bool] = None,
    ):
        self.question: str = question
        self.question_mark: str = question_mark
        self.default_choice: Optional[bool] = default_choice

    def _reset(self):
        self._answered: bool = False
        self._buffer: Buffer = Buffer(
            validator=Validator.from_callable(self._validate),
            name=DEFAULT_BUFFER,
            accept_handler=self._submit,
        )

    def _build_layout(self) -> Layout:
        self._reset()
        layout = Layout(
            HSplit(
                [
                    Window(
                        BufferControl(
                            self._buffer, lexer=SimpleLexer("class:answer")
                        ),
                        dont_extend_height=True,
                        get_line_prefix=self._get_prompt,
                    )
                ]
            )
        )
        return layout

    def _build_style(self, style: Style) -> Style:
        default = Style(
            [
                ("questionmark", "fg:#5F819D"),
                ("question", "bold"),
                ("answer", "fg:#5F819D"),
            ]
        )
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._buffer.validate_and_handle()

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            event.app.exit(result=NoAnswer)

        return kb

    def _get_prompt(
        self, line_number: int, wrap_count: int
    ) -> AnyFormattedText:
        prompt = [
            ("class:questionmark", self.question_mark),
            ("", " "),
            ("class:question", self.question.strip()),
            ("", " "),
        ]
        if not self._answered:
            if self.default_choice:
                prompt.append(("class:annotation", "(Y/n)"))
            elif self.default_choice == False:
                prompt.append(("class:annotation", "(y/N)"))
            else:
                prompt.append(("class:annotation", "(y/n)"))
            prompt.append(("", " "))
        return prompt

    def _validate(self, input: str) -> bool:
        if not input and self.default_choice is None:
            return False
        elif input and input.lower() not in ["y", "yes", "n", "no"]:
            return False
        return True

    def _submit(self, buffer: Buffer) -> bool:
        self._answered = True
        input = buffer.document.text
        if not input:
            buffer.document.insert_after(str(self.default_choice))
            get_app().exit(result=self.default_choice)
        elif input.lower() in ["y", "yes"]:
            get_app().exit(result=True)
        else:
            get_app().exit(result=False)
        return True
