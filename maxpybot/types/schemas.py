from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional

from pydantic import model_validator

from .base import MaxBaseModel
from .generated.models import (
    AttachmentRequest,
    BotCommand,
    ChatAdmin,
    NewMessageLink,
    SenderAction,
    TextFormat,
)


class BotPatchSchema(MaxBaseModel):
    commands: Optional[List[BotCommand]] = None
    description: Optional[str] = None
    first_name: Optional[str] = None
    name: Optional[str] = None
    photo: Optional[Any] = None


class ChatPatchSchema(MaxBaseModel):
    icon: Optional[Any] = None
    notify: Optional[bool] = None
    pin: Optional[str] = None
    title: Optional[str] = None


class SendActionSchema(MaxBaseModel):
    action: SenderAction = ...


class PinMessageSchema(MaxBaseModel):
    message_id: str = ...
    notify: Optional[bool] = None


class ChatAdminsSchema(MaxBaseModel):
    admins: List[ChatAdmin] = ...


class UserIdsSchema(MaxBaseModel):
    user_ids: Any = ...


class NewMessageSchema(MaxBaseModel):
    attachments: Optional[List[AttachmentRequest]] = None
    format: Optional[TextFormat] = None
    link: Optional[NewMessageLink] = None
    notify: Optional[bool] = None
    text: Optional[str] = None


class CallbackAnswerSchema(MaxBaseModel):
    message: Optional[Any] = None
    notification: Optional[str] = None


class SubscriptionSchema(MaxBaseModel):
    secret: Optional[str] = None
    update_types: Optional[List[str]] = None
    url: str = ...
    version: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _compat_aliases(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        legacy_url = payload.pop("subscribe_url", None)
        if legacy_url is not None and "url" not in payload:
            warnings.warn(
                "`subscribe_url` is deprecated in SubscriptionSchema, use `url`.",
                DeprecationWarning,
                stacklevel=2,
            )
            payload["url"] = legacy_url
        return payload
