from __future__ import annotations

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
        message = _as_dict(_extract_message(update))
        if not message:
            return False
        body = _as_dict(message.get("body"))
        if not body:
            return False
        text = str(body.get("text") or "")
        return needle in text

    return _predicate


def _extract_message(update: Any) -> Any:
    if isinstance(update, dict):
        return update.get("message")
    return getattr(update, "message", None)


def _as_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    return {}
