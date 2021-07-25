import abc
from typing import Any, Union, Generic, TypeVar, Optional
from dataclasses import dataclass

from prompt_toolkit.styles import Style
from prompt_toolkit.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application

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

    def _build_application(self, style: Style) -> Application:
        return Application(layout=self._build_layout(),
                           style=self._build_style(style),
                           key_bindings=self._build_keybindings())

    def prompt(self,
               default: DT = None,
               style: Optional[Style] = None) -> Union[DT, RT]:
        app = self._build_application(style=style or Style([]))
        result: RT = app.run()
        if result is NoAnswer:
            if default is None:
                raise RuntimeError("No answer selected!")
            return default
        else:
            return result


class NoAnswer:
    pass


@dataclass
class Choice:
    name: str
