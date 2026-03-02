from maxpybot.types import Chat, Message, User
from maxpybot.types.generated.runtime import validate_with_model


def test_public_dto_imports_are_available() -> None:
    assert User.__name__ == "User"
    assert Chat.__name__ == "Chat"
    assert Message.__name__ == "Message"


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
