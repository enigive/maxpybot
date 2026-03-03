from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union

from .base import MaxBaseModel
from .generated.models import (
    Callback as _Callback,
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
    MessageBody as _MessageBody,
    MessageCallbackUpdate as _MessageCallbackUpdate,
    MessageChatCreatedUpdate as _MessageChatCreatedUpdate,
    MessageCreatedUpdate as _MessageCreatedUpdate,
    MessageEditedUpdate as _MessageEditedUpdate,
    MessageList as _MessageList,
    MessageRemovedUpdate as _MessageRemovedUpdate,
    PhotoTokens as _PhotoTokens,
    Recipient as _Recipient,
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

if TYPE_CHECKING:
    from ..api_client import MaxBot


class User(_User):
    """Public user DTO."""


class AttachmentType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    CONTACT = "contact"
    INLINE_KEYBOARD = "inline_keyboard"
    SHARE = "share"
    LOCATION = "location"


class ChatIcon(MaxBaseModel):
    url: Optional[str] = None


class MessageSender(MaxBaseModel):
    user_id: Optional[int] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: Optional[bool] = None
    last_activity_time: Optional[int] = None


class MessageStat(MaxBaseModel):
    views: Optional[int] = None


class MessageLink(MaxBaseModel):
    chat_id: Optional[int] = None
    message: Optional[Union["Message", "MessageLink"]] = None
    sender: Optional[MessageSender] = None
    type: Optional[str] = None


class Chat(_Chat):
    """Public chat DTO."""

    dialog_with_user: Optional[Union[User, MessageSender]] = None
    icon: Optional[ChatIcon] = None
    participants: Optional[Dict[str, object]] = None
    pinned_message: Optional[Union["Message", MessageLink]] = None
    status: str
    type: str


class Recipient(_Recipient):
    chat_type: str


class MessageBody(_MessageBody):
    pass


class Message(_Message):
    """Public message DTO."""

    body: MessageBody
    link: Optional[MessageLink] = None
    recipient: Recipient
    sender: Optional[MessageSender] = None
    stat: Optional[MessageStat] = None

    @property
    def chat(self) -> Recipient:
        return self.recipient

    @property
    def start_payload(self) -> Optional[str]:
        text = str(getattr(self.body, "text", "") or "").strip()
        if not text:
            return None

        parts = text.split(None, 1)
        command = parts[0]
        if command != "/start" and not command.startswith("/start@"):
            return None
        if len(parts) < 2:
            return None

        payload = parts[1].strip()
        if not payload:
            return None
        return payload

    async def answer(
        self,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_message(
            chat_id=self.chat.chat_id,
            text=text,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
            inline_keyboard=inline_keyboard,
            reply_keyboard=reply_keyboard,
        )

    async def answer_image(
        self,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["PhotoTokens"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_image(
            chat_id=self.chat.chat_id,
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
            caption=caption,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
            inline_keyboard=inline_keyboard,
            reply_keyboard=reply_keyboard,
        )

    async def answer_video(
        self,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_video(
            chat_id=self.chat.chat_id,
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
            caption=caption,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
            inline_keyboard=inline_keyboard,
            reply_keyboard=reply_keyboard,
        )

    async def answer_audio(
        self,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_audio(
            chat_id=self.chat.chat_id,
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
            caption=caption,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )

    async def answer_file(
        self,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        token: Optional[str] = None,
        uploaded: Optional["UploadedInfo"] = None,
        caption: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_file(
            chat_id=self.chat.chat_id,
            file_path=file_path,
            url=url,
            token=token,
            uploaded=uploaded,
            caption=caption,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )

    async def answer_sticker(
        self,
        code: str,
        notify: bool = True,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_sticker(
            chat_id=self.chat.chat_id,
            code=code,
            notify=notify,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )

    async def answer_contact(
        self,
        name: str,
        contact_id: Optional[int] = None,
        vcf_phone: Optional[str] = None,
        vcf_info: Optional[str] = None,
        notify: bool = True,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_contact(
            chat_id=self.chat.chat_id,
            name=name,
            contact_id=contact_id,
            vcf_phone=vcf_phone,
            vcf_info=vcf_info,
            notify=notify,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
        )

    async def answer_location(
        self,
        latitude: float,
        longitude: float,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_location(
            chat_id=self.chat.chat_id,
            latitude=latitude,
            longitude=longitude,
            text=text,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
            inline_keyboard=inline_keyboard,
            reply_keyboard=reply_keyboard,
        )

    async def answer_share(
        self,
        url: str,
        text: str = "",
        notify: bool = True,
        format: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        forward_message_id: Optional[str] = None,
        inline_keyboard: Optional["InlineKeyboard"] = None,
        reply_keyboard: Optional["ReplyKeyboard"] = None,
    ) -> Any:
        if self.bot is None:
            raise RuntimeError("bot instance is not available in this message")
        return await self.bot.send_share(
            chat_id=self.chat.chat_id,
            url=url,
            text=text,
            notify=notify,
            format=format,
            reply_to_message_id=reply_to_message_id,
            forward_message_id=forward_message_id,
            inline_keyboard=inline_keyboard,
            reply_keyboard=reply_keyboard,
        )


class Callback(_Callback):
    user: User
    message: Optional["Message"] = None

    @property
    def chat(self) -> Optional[Recipient]:
        if self.message is None:
            return None
        return self.message.chat

    async def answer(self, notification: str, bot: Optional["MaxBot"] = None) -> Any:
        notification_text = str(notification or "").strip()
        if not notification_text:
            raise ValueError("notification is empty")

        target_bot = bot or self.bot
        if target_bot is None:
            raise RuntimeError("bot instance is not available in this callback")

        return await target_bot.messages.answer_on_callback(
            callback_id=self.callback_id,
            callback={"notification": notification_text},
        )


class BotInfo(_BotInfo):
    pass


class ChatList(_ChatList):
    pass


class ChatMember(_ChatMember):
    permissions: List[str]


class ChatMembersList(_ChatMembersList):
    pass


class GetPinnedMessageResult(_GetPinnedMessageResult):
    message: Optional[Union[Message, MessageLink]] = None


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
    photos: Dict[str, object]


class VideoAttachmentDetails(_VideoAttachmentDetails):
    thumbnail: Optional[Union[Dict[str, object], str]] = None
    urls: Optional[Dict[str, object]] = None


class Update(_Update):
    pass


class MessageCallbackUpdate(_MessageCallbackUpdate):
    callback: Callback
    message: Optional[Message]


class MessageCreatedUpdate(_MessageCreatedUpdate):
    message: Message


class MessageRemovedUpdate(_MessageRemovedUpdate):
    pass


class MessageEditedUpdate(_MessageEditedUpdate):
    message: Message


class BotAddedToChatUpdate(_BotAddedToChatUpdate):
    user: User


class BotRemovedFromChatUpdate(_BotRemovedFromChatUpdate):
    user: User


class UserAddedToChatUpdate(_UserAddedToChatUpdate):
    user: User


class UserRemovedFromChatUpdate(_UserRemovedFromChatUpdate):
    user: User


class BotStartedUpdate(_BotStartedUpdate):
    user: User

    @property
    def start_payload(self) -> Optional[str]:
        payload = getattr(self, "payload", None)
        if payload is None:
            return None
        payload_text = str(payload).strip()
        if not payload_text:
            return None
        return payload_text


class ChatTitleChangedUpdate(_ChatTitleChangedUpdate):
    user: User


class MessageChatCreatedUpdate(_MessageChatCreatedUpdate):
    chat: Chat


class DialogLifecycleUpdate(MaxBaseModel):
    chat_id: Optional[int] = None
    timestamp: int
    update_type: str
    user: Optional[User] = None
    user_locale: Optional[str] = None
    user_id: Optional[int] = None


class BotStoppedUpdate(DialogLifecycleUpdate):
    pass


class DialogMutedUpdate(DialogLifecycleUpdate):
    pass


class DialogUnmutedUpdate(DialogLifecycleUpdate):
    pass


class DialogClearedUpdate(DialogLifecycleUpdate):
    pass


class DialogRemovedUpdate(DialogLifecycleUpdate):
    pass


class UnknownUpdate(MaxBaseModel):
    update_type: Optional[str] = None
    timestamp: Optional[int] = None
    parse_error: Optional[str] = None


_PUBLIC_DTO_CLASSES: Tuple[Type[MaxBaseModel], ...] = (
    User,
    ChatIcon,
    MessageSender,
    MessageStat,
    MessageLink,
    Chat,
    Recipient,
    MessageBody,
    Message,
    Callback,
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
    DialogLifecycleUpdate,
    BotStoppedUpdate,
    DialogMutedUpdate,
    DialogUnmutedUpdate,
    DialogClearedUpdate,
    DialogRemovedUpdate,
    UnknownUpdate,
)

PUBLIC_DTO_BY_NAME: Dict[str, Type[MaxBaseModel]] = {
    dto.__name__: dto for dto in _PUBLIC_DTO_CLASSES
}

