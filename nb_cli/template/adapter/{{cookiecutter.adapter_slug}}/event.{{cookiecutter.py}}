from typing_extensions import override

from pydantic import BaseModel
from nonebot.adapters import Event as BaseEvent

from .message import Message


class Event(BaseEvent):

    @override
    def get_type(self) -> str:
        raise NotImplementedError

    @override
    def get_event_name(self) -> str:
        raise NotImplementedError

    @override
    def get_event_description(self) -> str:
        return str(self.dict())

    @override
    def get_message(self) -> Message:
        raise NotImplementedError

    @override
    def get_plaintext(self) -> str:
        raise NotImplementedError

    @override
    def get_user_id(self) -> str:
        raise NotImplementedError

    @override
    def get_session_id(self) -> str:
        raise NotImplementedError

    @override
    def is_tome(self) -> bool:
        return False
