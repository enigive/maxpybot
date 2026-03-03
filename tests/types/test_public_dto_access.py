from maxpybot.types import (
    AttachmentType,
    BotStartedUpdate,
    BotStoppedUpdate,
    Callback,
    Chat,
    ChatIcon,
    Message,
    MessageCallbackUpdate,
    MessageSender,
    User,
)
from maxpybot.types.generated.runtime import validate_with_model


def test_public_dto_imports_are_available() -> None:
    assert User.__name__ == "User"
    assert Chat.__name__ == "Chat"
    assert Message.__name__ == "Message"


def test_attachment_type_enum_has_only_supported_values() -> None:
    assert {item.value for item in AttachmentType} == {
        "image",
        "video",
        "audio",
        "file",
        "sticker",
        "contact",
        "inline_keyboard",
        "share",
        "location",
    }


def test_runtime_prefers_public_user_dto() -> None:
    payload = {
        "first_name": "Alice",
        "is_bot": False,
        "last_activity_time": 1710000000,
        "last_name": "Doe",
        "user_id": "100",
        "username": "alice",
    }

    parsed = validate_with_model("User", payload)

    assert isinstance(parsed, User)
    assert parsed.__class__ is User


def test_runtime_prefers_public_chat_and_message_dto() -> None:
    chat_payload = {
        "chat_id": 200,
        "description": "Chat",
        "icon": {},
        "is_public": False,
        "last_event_time": 1710000000,
        "participants_count": 2,
        "status": "active",
        "title": "General",
        "type": "chat",
    }
    message_payload = {
        "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
        "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
        "timestamp": 1710000000,
    }

    parsed_chat = validate_with_model("Chat", chat_payload)
    parsed_message = validate_with_model("Message", message_payload)

    assert isinstance(parsed_chat, Chat)
    assert parsed_chat.__class__ is Chat
    assert isinstance(parsed_message, Message)
    assert parsed_message.__class__ is Message


def test_runtime_prefers_public_dialog_lifecycle_dto() -> None:
    payload = {
        "update_type": "bot_stopped",
        "timestamp": 1710000000,
        "chat_id": 200,
        "user_id": 100,
    }

    parsed = validate_with_model("BotStoppedUpdate", payload)

    assert isinstance(parsed, BotStoppedUpdate)
    assert parsed.__class__ is BotStoppedUpdate


def test_public_message_has_chat_property() -> None:
    payload = {
        "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
        "recipient": {"chat_id": 777, "chat_type": "chat", "user_id": 0},
        "timestamp": 1710000000,
    }
    message = validate_with_model("Message", payload)
    assert isinstance(message, Message)
    assert message.chat.chat_id == 777


def test_public_message_sender_stat_and_link_use_typed_models() -> None:
    payload = {
        "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
        "recipient": {"chat_id": 777, "chat_type": "chat", "user_id": 0},
        "sender": {"user_id": 42, "name": "Alice"},
        "link": {"chat_id": 700, "type": "reply", "message": {"mid": "m-link"}},
        "stat": {"views": 12},
        "timestamp": 1710000000,
    }
    message = validate_with_model("Message", payload)
    assert isinstance(message, Message)
    assert isinstance(message.sender, MessageSender)
    assert message.sender.user_id == 42
    assert message.recipient.chat_type == "chat"
    assert message.stat is not None
    assert message.link is not None


def test_public_chat_uses_typed_icon_without_any() -> None:
    payload = {
        "chat_id": 200,
        "description": "Chat",
        "icon": {},
        "is_public": False,
        "last_event_time": 1710000000,
        "participants_count": 2,
        "status": "active",
        "title": "General",
        "type": "chat",
    }

    chat = validate_with_model("Chat", payload)
    assert isinstance(chat, Chat)
    assert isinstance(chat.icon, ChatIcon)
    assert isinstance(chat.status, str)
    assert isinstance(chat.type, str)


def test_public_message_exposes_start_payload_property() -> None:
    payload = {
        "body": {"mid": "m-1", "seq": 1, "text": "/start ref_user456789", "attachments": []},
        "recipient": {"chat_id": 777, "chat_type": "chat", "user_id": 0},
        "timestamp": 1710000000,
    }
    message = validate_with_model("Message", payload)
    assert isinstance(message, Message)
    assert message.start_payload == "ref_user456789"


def test_bot_started_update_exposes_start_payload_property() -> None:
    payload = {
        "update_type": "bot_started",
        "timestamp": 1710000000,
        "chat_id": 1234567890,
        "user": {
            "first_name": "Ivan",
            "is_bot": False,
            "last_activity_time": 1710000000,
            "last_name": "Petrov",
            "user_id": "100",
            "username": "ivan",
        },
        "payload": "promo_summer2025",
    }
    update = validate_with_model("BotStartedUpdate", payload)
    assert isinstance(update, BotStartedUpdate)
    assert update.start_payload == "promo_summer2025"


def test_message_callback_update_uses_typed_callback_and_message() -> None:
    payload = {
        "update_type": "message_callback",
        "timestamp": 1710000000,
        "callback": {
            "callback_id": "cb-1",
            "payload": "ok",
            "timestamp": 1710000000,
            "user": {
                "first_name": "A",
                "is_bot": False,
                "last_activity_time": 1710000000,
                "last_name": "B",
                "user_id": "100",
                "username": "alice",
            },
        },
        "message": {
            "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
            "recipient": {"chat_id": 333, "chat_type": "chat", "user_id": 0},
            "timestamp": 1710000000,
        },
    }

    parsed = validate_with_model("MessageCallbackUpdate", payload)
    assert isinstance(parsed, MessageCallbackUpdate)
    assert isinstance(parsed.callback, Callback)
    assert isinstance(parsed.message, Message)
