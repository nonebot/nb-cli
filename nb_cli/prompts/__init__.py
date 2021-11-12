import abc
from dataclasses import dataclass
from typing import Union, Generic, TypeVar, Optional

from prompt_toolkit.layout import Layout
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Attrs, Style, StyleTransformation

DT = TypeVar("DT")
RT = TypeVar("RT")


class BasePrompt(abc.ABC, Generic[RT]):
    @abc.abstractmethod
    def _build_layout(self) -> Layout:
        raise NotImplementedError

    @abc.abstractmethod
    def _build_style(self, style: Style) -> Style:
        raise NotImplementedError

    @abc.abstractmethod
    def _build_keybindings(self) -> KeyBindings:
        raise NotImplementedError

    def _build_application(self, no_ansi: bool, style: Style) -> Application:
        return Application(
            layout=self._build_layout(),
            style=self._build_style(style),
            style_transformation=DisableColorTransformation(no_ansi),
            key_bindings=self._build_keybindings(),
            mouse_support=True,
        )

    def prompt(
        self,
        default: DT = None,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> Union[DT, RT]:
        app = self._build_application(no_ansi=no_ansi, style=style or Style([]))
        result: RT = app.run()
        if result is NoAnswer:
            if default is None:
                raise CanceledError("No answer selected!")
            return default
        else:
            return result


class NoAnswer:
    pass


class CanceledError(Exception):
    """User cancelled answer."""


@dataclass
class Choice(Generic[RT]):
    name: str
    data: RT = None  # type: ignore


class DisableColorTransformation(StyleTransformation):
    def __init__(self, no_ansi: bool = False):
        self.no_ansi = no_ansi

    def transform_attrs(self, attrs: Attrs) -> Attrs:
        if self.no_ansi:
            return Attrs(
                "", "", False, False, False, False, False, False, False
            )
        return attrs


from .list import ListPrompt
from .input import InputPrompt
from .confirm import ConfirmPrompt
from .checkbox import CheckboxPrompt
