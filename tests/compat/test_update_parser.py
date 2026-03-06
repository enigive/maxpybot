import warnings
from typing import Any, Dict

import pytest

from maxpybot.compat.capabilities import CAPABILITY_MATRIX, detect_payload_capabilities, supported_capabilities
from maxpybot.compat.attachments import ATTACHMENT_MODEL_BY_TYPE, normalize_message_attachments
from maxpybot.compat.update_parser import UpdateParser
from maxpybot.types import (
    AttachmentType,
    BotStoppedUpdate,
    DialogClearedUpdate,
    DialogMutedUpdate,
    DialogRemovedUpdate,
    DialogUnmutedUpdate,
    UnknownUpdate,
)


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


def test_parse_message_created_update_without_text_or_attachments() -> None:
    parser = UpdateParser()
    raw_update = {
        "update_type": "message_created",
        "timestamp": 1710000000000,
        "message": {
            "sender": {"user_id": 100, "name": "Alice"},
            "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
            "timestamp": 1710000000000,
            "body": {
                "mid": "m-empty",
                "seq": 1,
            },
        },
    }

    parsed = parser.parse_update(raw_update)
    assert not isinstance(parsed, UnknownUpdate)

    parsed_dict = _as_dict(parsed)
    message = _as_dict(parsed_dict.get("message"))
    body = _as_dict(message.get("body"))

    assert body.get("attachments") == []
    assert body.get("text") is None


def test_attachment_parser_mapping_uses_only_enum_types() -> None:
    assert set(ATTACHMENT_MODEL_BY_TYPE.keys()) == set(AttachmentType)


def test_parse_unknown_update_type_returns_unknown_update_model() -> None:
    parser = UpdateParser()
    raw_update = {"update_type": "some_new_update", "timestamp": 1, "x": 42}
    parsed = parser.parse_update(raw_update)

    assert isinstance(parsed, UnknownUpdate)
    parsed_dict = _as_dict(parsed)
    assert parsed_dict["update_type"] == "some_new_update"
    assert parsed_dict["raw_payload"]["x"] == 42
    assert "unsupported update_type" in str(parsed_dict.get("parse_error") or "")


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


def test_normalize_message_attachments_defaults_to_empty_list() -> None:
    payload = {
        "body": {
            "mid": "m-no-attachments",
            "seq": 1,
        }
    }

    normalized = normalize_message_attachments(payload)

    assert normalized["body"]["attachments"] == []


def test_message_callback_update_binds_message_inside_callback() -> None:
    parser = UpdateParser()
    parsed = parser.parse_update(
        {
            "update_type": "message_callback",
            "timestamp": 1710000000000,
            "callback": {
                "callback_id": "cb-1",
                "timestamp": 1710000000000,
                "user": {
                    "first_name": "Alice",
                    "is_bot": False,
                    "last_activity_time": 1710000000000,
                    "last_name": "Doe",
                    "user_id": "100",
                    "username": "alice",
                },
                "payload": "approve",
            },
            "message": {
                "sender": {
                    "first_name": "Bot",
                    "is_bot": True,
                    "last_activity_time": 1710000000000,
                    "last_name": "X",
                    "user_id": "1",
                    "username": "bot",
                },
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 100},
                "timestamp": 1710000000000,
                "body": {
                    "mid": "m-1",
                    "seq": 1,
                    "text": "hello",
                    "attachments": [],
                },
            },
        }
    )

    callback = getattr(parsed, "callback", None)
    assert callback is not None
    assert getattr(callback, "message", None) is not None
    assert getattr(callback.message.chat, "chat_id", None) == 200


@pytest.mark.parametrize(
    ("update_type", "expected_class"),
    [
        ("bot_stopped", BotStoppedUpdate),
        ("dialog_muted", DialogMutedUpdate),
        ("dialog_unmuted", DialogUnmutedUpdate),
        ("dialog_cleared", DialogClearedUpdate),
        ("dialog_removed", DialogRemovedUpdate),
    ],
)
def test_dialog_lifecycle_updates_use_public_dto_classes(update_type: str, expected_class: Any) -> None:
    parser = UpdateParser()
    parsed = parser.parse_update(
        {
            "update_type": update_type,
            "timestamp": 1710000000000,
            "chat_id": 200,
            "user_id": 100,
        }
    )

    assert isinstance(parsed, expected_class)
    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("chat_id") == 200
    assert parsed_dict.get("user_id") == 100


@pytest.mark.parametrize(
    "update_type",
    [
        "bot_stopped",
        "dialog_muted",
        "dialog_unmuted",
        "dialog_cleared",
        "dialog_removed",
    ],
)
def test_dialog_lifecycle_old_aliases_are_normalized_with_deprecation_warning(update_type: str) -> None:
    parser = UpdateParser()
    with pytest.warns(DeprecationWarning, match="deprecated"):
        parsed = parser.parse_update(
            {
                "update_type": update_type,
                "timestamp": 1710000000000,
                "dialog_id": 300,
                "userId": 400,
            }
        )

    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("chat_id") == 300
    assert parsed_dict.get("user_id") == 400
    assert parsed_dict.get("raw_payload", {}).get("dialog_id") == 300
    assert parsed_dict.get("raw_payload", {}).get("userId") == 400


def test_dialog_lifecycle_nested_legacy_payload_is_normalized_and_warned() -> None:
    parser = UpdateParser()
    with pytest.warns(DeprecationWarning, match="deprecated"):
        parsed = parser.parse_update(
            {
                "update_type": "dialog_muted",
                "timestamp": 1710000000000,
                "dialog": {"id": 500, "with_user_id": 600},
                "user": {"user_id": 600},
            }
        )

    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("chat_id") == 500
    assert parsed_dict.get("user_id") == 600


def test_dialog_lifecycle_canonical_payload_with_user_and_locale_no_deprecation_warning() -> None:
    parser = UpdateParser()
    payload = {
        "update_type": "dialog_unmuted",
        "timestamp": 1710000000000,
        "chat_id": 500,
        "user": {
            "first_name": "Alice",
            "is_bot": False,
            "last_activity_time": 1710000000000,
            "last_name": "Doe",
            "user_id": "600",
            "username": "alice",
        },
        "user_locale": "ru-RU",
    }

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        parsed = parser.parse_update(payload)

    deprecations = [item for item in captured if issubclass(item.category, DeprecationWarning)]
    assert deprecations == []

    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("chat_id") == 500
    assert parsed_dict.get("user_locale") == "ru-RU"
    assert parsed_dict.get("user_id") == 600
    assert _as_dict(parsed_dict.get("user")).get("username") == "alice"


def test_capability_matrix_for_dialog_lifecycle_updates_is_declared() -> None:
    for update_type in ("bot_stopped", "dialog_muted", "dialog_unmuted", "dialog_cleared", "dialog_removed"):
        assert update_type in CAPABILITY_MATRIX
        assert supported_capabilities(update_type)


def test_detect_payload_capabilities_handles_legacy_and_new_formats() -> None:
    legacy_payload = {"dialog_id": 10, "userId": 20}
    new_payload = {"chat_id": 10, "user_id": 20}
    bot_stopped_payload = {"chat_id": 10, "payload": "legacy"}
    locale_payload = {"chat_id": 10, "user_locale": "en-US"}

    legacy_caps = detect_payload_capabilities("dialog_muted", legacy_payload)
    new_caps = detect_payload_capabilities("dialog_muted", new_payload)
    bot_stopped_caps = detect_payload_capabilities("bot_stopped", bot_stopped_payload)
    locale_caps = detect_payload_capabilities("dialog_muted", locale_payload)

    assert "dialog_legacy_ids" in legacy_caps
    assert "dialog_flat_ids" not in legacy_caps
    assert "dialog_flat_ids" in new_caps
    assert "bot_stopped_payload" in bot_stopped_caps
    assert "dialog_user_locale" in locale_caps


def test_parser_attaches_detected_and_supported_capabilities() -> None:
    parser = UpdateParser()
    parsed = parser.parse_update(
        {
            "update_type": "dialog_removed",
            "timestamp": 1710000000000,
            "chat_id": 42,
            "user_id": 24,
            "user_locale": "en-US",
        }
    )
    parsed_dict = _as_dict(parsed)

    assert "dialog_flat_ids" in parsed_dict.get("compat_capabilities", [])
    assert "dialog_user_locale" in parsed_dict.get("compat_capabilities", [])
    assert "dialog_nested_dialog" in parsed_dict.get("compat_supported_capabilities", [])


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
        "message_chat_created",
    ],
)
def test_parser_accepts_known_update_types(update_type: str) -> None:
    parser = UpdateParser()
    parsed = parser.parse_update({"update_type": update_type, "timestamp": 1})
    parsed_dict = _as_dict(parsed)
    assert parsed_dict.get("update_type") == update_type
