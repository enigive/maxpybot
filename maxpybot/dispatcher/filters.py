from __future__ import annotations

import re
from typing import Any, Callable


def update_type_is(expected: str) -> Callable[[Any], bool]:
    def _predicate(update: Any) -> bool:
        if isinstance(update, dict):
            value = update.get("update_type")
        else:
            value = getattr(update, "update_type", None)
        return str(value or "") == expected

    return _predicate


def chat_id_is(expected_chat_id: int) -> Callable[[Any], bool]:
    def _predicate(update: Any) -> bool:
        message = _as_dict(_extract_message(update))
        if not message:
            return False
        recipient = _as_dict(message.get("recipient"))
        if not recipient:
            return False
        return int(recipient.get("chat_id") or 0) == int(expected_chat_id)

    return _predicate


def text_contains(needle: str) -> Callable[[Any], bool]:
    def _predicate(update: Any) -> bool:
        text = _extract_message_text(update)
        return needle in text

    return _predicate


def text_matches(pattern: str, flags: int = 0) -> Callable[[Any], bool]:
    regex = re.compile(pattern, flags)

    def _predicate(update: Any) -> bool:
        text = _extract_message_text(update)
        if not text:
            return False
        return bool(regex.search(text))

    return _predicate


def chat_type_is(expected_chat_type: str) -> Callable[[Any], bool]:
    def _predicate(update: Any) -> bool:
        message = _as_dict(_extract_message(update))
        if not message:
            return False
        recipient = _as_dict(message.get("recipient"))
        chat_type = str(recipient.get("chat_type") or "")
        return chat_type == expected_chat_type

    return _predicate


def sender_id_is(expected_sender_id: int) -> Callable[[Any], bool]:
    expected_id = int(expected_sender_id)

    def _predicate(update: Any) -> bool:
        sender = _extract_sender(update)
        if not sender:
            return False
        sender_id = _to_int(sender.get("user_id"))
        if sender_id is None:
            return False
        return sender_id == expected_id

    return _predicate


def callback_payload_is(expected_payload: str) -> Callable[[Any], bool]:
    def _predicate(update: Any) -> bool:
        callback = _as_dict(_extract_callback(update))
        if not callback:
            return False
        return str(callback.get("payload") or "") == expected_payload

    return _predicate


def _extract_message(update: Any) -> Any:
    if isinstance(update, dict):
        return update.get("message")
    return getattr(update, "message", None)


def _extract_callback(update: Any) -> Any:
    if isinstance(update, dict):
        return update.get("callback")
    return getattr(update, "callback", None)


def _extract_sender(update: Any) -> Any:
    message = _as_dict(_extract_message(update))
    if message:
        sender = _as_dict(message.get("sender"))
        if sender:
            return sender
    if isinstance(update, dict):
        return _as_dict(update.get("user"))
    return _as_dict(getattr(update, "user", None))


def _extract_message_text(update: Any) -> str:
    message = _as_dict(_extract_message(update))
    if not message:
        return ""
    body = _as_dict(message.get("body"))
    if not body:
        return ""
    return str(body.get("text") or "")


def _as_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    return {}


def _to_int(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
