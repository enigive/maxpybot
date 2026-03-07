from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from .base import MaxBaseModel


from pydantic import Field

class InlineKeyboardButton(MaxBaseModel):
    type: str = Field(...)
    text: str = Field(...)


class InlineCallbackButton(InlineKeyboardButton):
    type: Literal["callback"] = "callback"
    payload: str = Field(...)
    intent: Optional[str] = None


class InlineLinkButton(InlineKeyboardButton):
    type: Literal["link"] = "link"
    url: str = Field(...)


class InlineRequestContactButton(InlineKeyboardButton):
    type: Literal["request_contact"] = "request_contact"


class InlineRequestGeoLocationButton(InlineKeyboardButton):
    type: Literal["request_geo_location"] = "request_geo_location"
    quick: Optional[bool] = None


class InlineChatButton(InlineKeyboardButton):
    type: Literal["chat"] = "chat"
    chat_title: str = Field(...)
    chat_description: Optional[str] = None
    start_payload: Optional[str] = None
    uuid: Optional[int] = None


class InlineMessageButton(InlineKeyboardButton):
    type: Literal["message"] = "message"


class InlineOpenAppButton(InlineKeyboardButton):
    type: Literal["open_app"] = "open_app"
    web_app: Optional[str] = None
    contact_id: Optional[int] = None
    payload: Optional[str] = None


InlineButton = Union[
    InlineCallbackButton,
    InlineLinkButton,
    InlineRequestContactButton,
    InlineRequestGeoLocationButton,
    InlineChatButton,
    InlineMessageButton,
    InlineOpenAppButton,
]


class InlineKeyboard(MaxBaseModel):
    buttons: List[List[InlineButton]] = Field(...)

    @classmethod
    def row(cls, *buttons: InlineButton) -> List[InlineButton]:
        return list(buttons)

    @classmethod
    def from_rows(cls, *rows: Sequence[InlineButton]) -> "InlineKeyboard":
        return cls(buttons=[list(row) for row in rows])

    def to_attachment_request(self) -> Dict[str, Any]:
        return {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [button.model_dump(by_alias=True, exclude_none=True) for button in row] for row in self.buttons
                ]
            },
        }


class ReplyKeyboardButton(MaxBaseModel):
    type: str = Field(...)
    text: str = Field(...)
    payload: Optional[str] = None


class ReplyMessageButton(ReplyKeyboardButton):
    type: Literal["message"] = "message"
    intent: Optional[str] = None


class ReplyGeoLocationButton(ReplyKeyboardButton):
    type: Literal["user_geo_location"] = "user_geo_location"
    quick: Optional[bool] = None


class ReplyContactButton(ReplyKeyboardButton):
    type: Literal["user_contact"] = "user_contact"


ReplyButton = Union[ReplyMessageButton, ReplyGeoLocationButton, ReplyContactButton]


class ReplyKeyboard(MaxBaseModel):
    buttons: List[List[ReplyButton]] = Field(...)
    direct: Optional[bool] = None
    direct_user_id: Optional[int] = None

    @classmethod
    def row(cls, *buttons: ReplyButton) -> List[ReplyButton]:
        return list(buttons)

    @classmethod
    def from_rows(
        cls,
        *rows: Sequence[ReplyButton],
        direct: Optional[bool] = None,
        direct_user_id: Optional[int] = None,
    ) -> "ReplyKeyboard":
        return cls(
            buttons=[list(row) for row in rows],
            direct=direct,
            direct_user_id=direct_user_id,
        )

    def to_attachment_request(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": "reply_keyboard",
            "buttons": [
                [button.model_dump(by_alias=True, exclude_none=True) for button in row] for row in self.buttons
            ],
        }
        if self.direct is not None:
            payload["direct"] = self.direct
        if self.direct_user_id is not None:
            payload["direct_user_id"] = self.direct_user_id
        return payload

