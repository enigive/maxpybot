from __future__ import annotations

from typing import Dict, Tuple, Type

from .base import MaxBaseModel
from .generated.models import (
    BotAddedToChatUpdate as _BotAddedToChatUpdate,
    BotInfo as _BotInfo,
    BotRemovedFromChatUpdate as _BotRemovedFromChatUpdate,
    BotStartedUpdate as _BotStartedUpdate,
    Chat as _Chat,
    ChatList as _ChatList,
    ChatMember as _ChatMember,
    ChatMembersList as _ChatMembersList,
    ChatTitleChangedUpdate as _ChatTitleChangedUpdate,
    GetPinnedMessageResult as _GetPinnedMessageResult,
    GetSubscriptionsResult as _GetSubscriptionsResult,
    Message as _Message,
    MessageCallbackUpdate as _MessageCallbackUpdate,
    MessageChatCreatedUpdate as _MessageChatCreatedUpdate,
    MessageCreatedUpdate as _MessageCreatedUpdate,
    MessageEditedUpdate as _MessageEditedUpdate,
    MessageList as _MessageList,
    MessageRemovedUpdate as _MessageRemovedUpdate,
    PhotoTokens as _PhotoTokens,
    SendMessageResult as _SendMessageResult,
    SimpleQueryResult as _SimpleQueryResult,
    Subscription as _Subscription,
    Update as _Update,
    UploadEndpoint as _UploadEndpoint,
    UploadedInfo as _UploadedInfo,
    User as _User,
    UserAddedToChatUpdate as _UserAddedToChatUpdate,
    UserRemovedFromChatUpdate as _UserRemovedFromChatUpdate,
    VideoAttachmentDetails as _VideoAttachmentDetails,
)


class User(_User):
    """Public user DTO."""


class Chat(_Chat):
    """Public chat DTO."""


class Message(_Message):
    """Public message DTO."""


class BotInfo(_BotInfo):
    pass


class ChatList(_ChatList):
    pass


class ChatMember(_ChatMember):
    pass


class ChatMembersList(_ChatMembersList):
    pass


class GetPinnedMessageResult(_GetPinnedMessageResult):
    pass


class MessageList(_MessageList):
    pass


class SendMessageResult(_SendMessageResult):
    pass


class SimpleQueryResult(_SimpleQueryResult):
    pass


class GetSubscriptionsResult(_GetSubscriptionsResult):
    pass


class Subscription(_Subscription):
    pass


class UploadEndpoint(_UploadEndpoint):
    pass


class UploadedInfo(_UploadedInfo):
    pass


class PhotoTokens(_PhotoTokens):
    pass


class VideoAttachmentDetails(_VideoAttachmentDetails):
    pass


class Update(_Update):
    pass


class MessageCallbackUpdate(_MessageCallbackUpdate):
    pass


class MessageCreatedUpdate(_MessageCreatedUpdate):
    pass


class MessageRemovedUpdate(_MessageRemovedUpdate):
    pass


class MessageEditedUpdate(_MessageEditedUpdate):
    pass


class BotAddedToChatUpdate(_BotAddedToChatUpdate):
    pass


class BotRemovedFromChatUpdate(_BotRemovedFromChatUpdate):
    pass


class UserAddedToChatUpdate(_UserAddedToChatUpdate):
    pass


class UserRemovedFromChatUpdate(_UserRemovedFromChatUpdate):
    pass


class BotStartedUpdate(_BotStartedUpdate):
    pass


class ChatTitleChangedUpdate(_ChatTitleChangedUpdate):
    pass


class MessageChatCreatedUpdate(_MessageChatCreatedUpdate):
    pass


_PUBLIC_DTO_CLASSES: Tuple[Type[MaxBaseModel], ...] = (
    User,
    Chat,
    Message,
    BotInfo,
    ChatList,
    ChatMember,
    ChatMembersList,
    GetPinnedMessageResult,
    MessageList,
    SendMessageResult,
    SimpleQueryResult,
    GetSubscriptionsResult,
    Subscription,
    UploadEndpoint,
    UploadedInfo,
    PhotoTokens,
    VideoAttachmentDetails,
    Update,
    MessageCallbackUpdate,
    MessageCreatedUpdate,
    MessageRemovedUpdate,
    MessageEditedUpdate,
    BotAddedToChatUpdate,
    BotRemovedFromChatUpdate,
    UserAddedToChatUpdate,
    UserRemovedFromChatUpdate,
    BotStartedUpdate,
    ChatTitleChangedUpdate,
    MessageChatCreatedUpdate,
)

PUBLIC_DTO_BY_NAME: Dict[str, Type[MaxBaseModel]] = {
    dto.__name__: dto for dto in _PUBLIC_DTO_CLASSES
}

