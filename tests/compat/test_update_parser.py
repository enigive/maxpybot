from typing import Any, Dict

import pytest

from maxpybot.compat.update_parser import UpdateParser


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    return {}


def test_parse_message_created_update_with_attachment_and_extra_fields() -> None:
    parser = UpdateParser(debug=True)
    raw_update = {
        "update_type": "message_created",
        "timestamp": 1710000000000,
        "new_platform_field": "future-value",
        "message": {
            "sender": {"user_id": 100, "name": "Alice"},
            "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
            "timestamp": 1710000000000,
            "body": {
                "mid": "m-1",
                "seq": 1,
                "text": "hello",
                "attachments": [
                    {
                        "type": "image",
                        "payload": {"url": "https://example.com/image.jpg"},
                    }
                ],
            },
        },
    }

    parsed = parser.parse_update(raw_update)
    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("update_type") == "message_created"
    assert parsed_dict.get("raw_payload", {}).get("new_platform_field") == "future-value"

    message = _as_dict(parsed_dict.get("message"))
    body = _as_dict(message.get("body"))
    attachments = body.get("attachments")
    assert isinstance(attachments, list)
    assert len(attachments) == 1
    assert _as_dict(attachments[0]).get("type") == "image"


def test_parse_unknown_update_type_returns_raw_dict() -> None:
    parser = UpdateParser()
    raw_update = {"update_type": "some_new_update", "timestamp": 1, "x": 42}
    parsed = parser.parse_update(raw_update)

    assert isinstance(parsed, dict)
    assert parsed["update_type"] == "some_new_update"
    assert parsed["raw_payload"]["x"] == 42


def test_parse_raw_attachments_compat_field() -> None:
    parser = UpdateParser()
    raw_update = {
        "update_type": "message_created",
        "timestamp": 1710000000000,
        "message": {
            "sender": {"user_id": 100, "name": "Alice"},
            "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
            "timestamp": 1710000000000,
            "body": {
                "mid": "m-raw",
                "seq": 1,
                "text": "legacy",
                "raw_attachments": [
                    {
                        "type": "image",
                        "payload": {"url": "https://example.com/legacy.jpg"},
                    }
                ],
            },
        },
    }

    parsed = parser.parse_update(raw_update)
    parsed_dict = _as_dict(parsed)
    message = _as_dict(parsed_dict.get("message"))
    body = _as_dict(message.get("body"))
    attachments = body.get("attachments")

    assert isinstance(attachments, list)
    assert len(attachments) == 1
    assert _as_dict(attachments[0]).get("type") == "image"


@pytest.mark.parametrize(
    "update_type",
    [
        "message_created",
        "message_callback",
        "message_edited",
        "message_removed",
        "bot_added",
        "bot_removed",
        "dialog_muted",
        "dialog_unmuted",
        "dialog_cleared",
        "dialog_removed",
        "user_added",
        "user_removed",
        "bot_started",
        "bot_stopped",
        "chat_title_changed",
    ],
)
def test_parser_accepts_known_update_types(update_type: str) -> None:
    parser = UpdateParser()
    parsed = parser.parse_update({"update_type": update_type, "timestamp": 1})
    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("update_type") == update_type
