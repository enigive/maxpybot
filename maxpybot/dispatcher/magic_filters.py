from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Pattern, Tuple, Union

from ..types import AttachmentType

FilterCallable = Callable[[Any], bool]

_MISSING = object()


class MagicFilter:
    """Composable sync filter expression."""

    def __init__(self, value_getter: Callable[[Any], Any]) -> None:
        self._value_getter = value_getter

    def _value(self, update: Any) -> Any:
        try:
            value = self._value_getter(update)
        except Exception:
            return _MISSING
        if value is None:
            return _MISSING
        return value

    def __call__(self, update: Any) -> bool:
        return _truthy(self._value(update))

    def __getattr__(self, name: str) -> "MagicFilter":
        if name.startswith("__"):
            raise AttributeError(name)
        return MagicFilter(lambda update: _resolve_attr(self._value(update), name))

    def __getitem__(self, key: str) -> "MagicFilter":
        return MagicFilter(lambda update: _resolve_item(self._value(update), key))

    def __invert__(self) -> "MagicFilter":
        return MagicFilter(lambda update: not self(update))

    def __and__(self, other: Any) -> "MagicFilter":
        other_filter = _coerce_filter(other)
        return MagicFilter(lambda update: self(update) and other_filter(update))

    def __rand__(self, other: Any) -> "MagicFilter":
        return _coerce_filter(other).__and__(self)

    def __or__(self, other: Any) -> "MagicFilter":
        other_filter = _coerce_filter(other)
        return MagicFilter(lambda update: self(update) or other_filter(update))

    def __ror__(self, other: Any) -> "MagicFilter":
        return _coerce_filter(other).__or__(self)

    def __eq__(self, other: Any) -> "MagicFilter":  # type: ignore[override]
        return MagicFilter(
            lambda update: _compare_eq(
                self._value(update),
                _resolve_other_value(other, update),
            )
        )

    def __ne__(self, other: Any) -> "MagicFilter":  # type: ignore[override]
        return MagicFilter(
            lambda update: _compare_ne(
                self._value(update),
                _resolve_other_value(other, update),
            )
        )

    def __lt__(self, other: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _compare_order(
                self._value(update),
                _resolve_other_value(other, update),
                "lt",
            )
        )

    def __le__(self, other: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _compare_order(
                self._value(update),
                _resolve_other_value(other, update),
                "le",
            )
        )

    def __gt__(self, other: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _compare_order(
                self._value(update),
                _resolve_other_value(other, update),
                "gt",
            )
        )

    def __ge__(self, other: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _compare_order(
                self._value(update),
                _resolve_other_value(other, update),
                "ge",
            )
        )

    def contains(self, needle: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _contains(
                self._value(update),
                _resolve_other_value(needle, update),
            )
        )

    def startswith(self, prefix: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _startswith(
                self._value(update),
                _resolve_other_value(prefix, update),
            )
        )

    def endswith(self, suffix: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _endswith(
                self._value(update),
                _resolve_other_value(suffix, update),
            )
        )

    def regexp(self, pattern: Union[str, Pattern[str]], flags: int = 0) -> "MagicFilter":
        regex = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        return MagicFilter(lambda update: _regexp(self._value(update), regex))

    def in_(self, values: Any) -> "MagicFilter":
        return MagicFilter(
            lambda update: _in_values(
                self._value(update),
                _resolve_other_value(values, update),
            )
        )

    def len(self) -> "MagicFilter":
        return MagicFilter(lambda update: _safe_len(self._value(update)))

    def lower(self) -> "MagicFilter":
        return MagicFilter(lambda update: _lower(self._value(update)))

    def upper(self) -> "MagicFilter":
        return MagicFilter(lambda update: _upper(self._value(update)))

    def strip(self) -> "MagicFilter":
        return MagicFilter(lambda update: _strip(self._value(update)))

    def __repr__(self) -> str:
        return "MagicFilter(<expr>)"


class _MagicRoot(MagicFilter):
    def __init__(self) -> None:
        super().__init__(lambda update: update)

    def __getattr__(self, name: str) -> MagicFilter:
        extractor = _ROOT_EXTRACTORS.get(name)
        if extractor is not None:
            return MagicFilter(extractor)
        return super().__getattr__(name)


F = _MagicRoot()


def update_type_is(expected: str) -> FilterCallable:
    return F.update_type == str(expected)


def chat_id_is(expected_chat_id: int) -> FilterCallable:
    return F.chat_id == int(expected_chat_id)


def text_contains(needle: str) -> FilterCallable:
    return F.text.contains(needle)


def text_matches(pattern: str, flags: int = 0) -> FilterCallable:
    return F.text.regexp(pattern, flags=flags)


def chat_type_is(expected_chat_type: str) -> FilterCallable:
    return F.chat.type == str(expected_chat_type)


def sender_id_is(expected_sender_id: int) -> FilterCallable:
    return F.sender.id == int(expected_sender_id)


def callback_payload_is(expected_payload: str) -> FilterCallable:
    return F.data == str(expected_payload)


def message_has_text() -> FilterCallable:
    return F.text


def message_has_attachment(attachment_type: Union[str, AttachmentType]) -> FilterCallable:
    expected = _to_attachment_type(attachment_type)
    if expected is None:
        return MagicFilter(lambda update: False)
    return MagicFilter(lambda update: _has_attachment(update, expected))


def message_has_sticker() -> FilterCallable:
    return F.sticker


def has_start_payload() -> FilterCallable:
    return F.start_payload


def start_payload_is(expected_payload: str) -> FilterCallable:
    return F.start_payload == str(expected_payload)


def start_payload_matches(pattern: str, flags: int = 0) -> FilterCallable:
    return F.start_payload.regexp(pattern, flags=flags)


def _coerce_filter(value: Any) -> MagicFilter:
    if isinstance(value, MagicFilter):
        return value
    if callable(value):
        return MagicFilter(lambda update: bool(value(update)))
    return MagicFilter(lambda update: value)


def _resolve_other_value(value: Any, update: Any) -> Any:
    if isinstance(value, MagicFilter):
        return value._value(update)
    return value


def _is_missing(value: Any) -> bool:
    return value is _MISSING


def _truthy(value: Any) -> bool:
    if _is_missing(value):
        return False
    return bool(value)


def _compare_eq(left: Any, right: Any) -> bool:
    if _is_missing(left) or _is_missing(right):
        return False
    return left == right


def _compare_ne(left: Any, right: Any) -> bool:
    if _is_missing(left) or _is_missing(right):
        return False
    return left != right


def _compare_order(left: Any, right: Any, op: str) -> bool:
    if _is_missing(left) or _is_missing(right):
        return False
    try:
        if op == "lt":
            return left < right
        if op == "le":
            return left <= right
        if op == "gt":
            return left > right
        if op == "ge":
            return left >= right
    except Exception:
        return False
    return False


def _contains(value: Any, needle: Any) -> bool:
    if _is_missing(value) or _is_missing(needle):
        return False
    if isinstance(value, str):
        return str(needle) in value
    try:
        return needle in value
    except Exception:
        return False


def _startswith(value: Any, prefix: Any) -> bool:
    if _is_missing(value) or _is_missing(prefix):
        return False
    return str(value).startswith(str(prefix))


def _endswith(value: Any, suffix: Any) -> bool:
    if _is_missing(value) or _is_missing(suffix):
        return False
    return str(value).endswith(str(suffix))


def _regexp(value: Any, regex: Pattern[str]) -> bool:
    if _is_missing(value):
        return False
    return bool(regex.search(str(value)))


def _in_values(value: Any, values: Any) -> bool:
    if _is_missing(value) or _is_missing(values):
        return False
    try:
        return value in values
    except Exception:
        return False


def _safe_len(value: Any) -> Any:
    if _is_missing(value):
        return _MISSING
    try:
        return len(value)
    except Exception:
        return _MISSING


def _lower(value: Any) -> Any:
    if _is_missing(value):
        return _MISSING
    return str(value).lower()


def _upper(value: Any) -> Any:
    if _is_missing(value):
        return _MISSING
    return str(value).upper()


def _strip(value: Any) -> Any:
    if _is_missing(value):
        return _MISSING
    return str(value).strip()


def _resolve_attr(value: Any, name: str) -> Any:
    if _is_missing(value):
        return _MISSING
    if isinstance(value, dict):
        if name in value:
            nested = value.get(name)
            if nested is None:
                return _MISSING
            return nested
        if name == "id":
            for candidate in ("chat_id", "user_id"):
                if candidate in value:
                    return value.get(candidate)
        if name == "type" and "chat_type" in value:
            return value.get("chat_type")
        if name == "data" and "payload" in value:
            return value.get("payload")
        return _MISSING

    direct = getattr(value, name, _MISSING)
    if direct is _MISSING and name == "id":
        for candidate in ("chat_id", "user_id"):
            direct = getattr(value, candidate, _MISSING)
            if direct is not _MISSING:
                break
    if direct is _MISSING and name == "type":
        direct = getattr(value, "chat_type", _MISSING)
    if direct is _MISSING and name == "data":
        direct = getattr(value, "payload", _MISSING)
    if direct is None:
        return _MISSING
    return direct


def _resolve_item(value: Any, key: str) -> Any:
    if _is_missing(value):
        return _MISSING
    if isinstance(value, dict):
        nested = value.get(key)
        if nested is None:
            return _MISSING
        return nested
    try:
        nested = value[key]
    except Exception:
        return _MISSING
    if nested is None:
        return _MISSING
    return nested


def _extract_update_type(update: Any) -> Optional[str]:
    value = getattr(update, "update_type", None)
    if isinstance(update, dict):
        value = update.get("update_type")
    if value is None:
        return None
    return str(value)


def _extract_message(update: Any) -> Any:
    value = getattr(update, "message", None)
    if isinstance(update, dict):
        value = update.get("message")
    return value


def _extract_message_attachments(update: Any) -> Any:
    message = _extract_message(update)
    if message is None:
        return []
    if isinstance(message, dict):
        body = message.get("body")
    else:
        body = getattr(message, "body", None)
    if body is None:
        return []
    if isinstance(body, dict):
        attachments = body.get("attachments")
    else:
        attachments = getattr(body, "attachments", None)
    if isinstance(attachments, list):
        return attachments
    return []


def _extract_attachment_type(value: Any) -> Optional[AttachmentType]:
    if isinstance(value, dict):
        raw_type = value.get("type")
    else:
        raw_type = getattr(value, "type", None)
    return _to_attachment_type(raw_type)


def _extract_callback(update: Any) -> Any:
    value = getattr(update, "callback", None)
    if isinstance(update, dict):
        value = update.get("callback")
    return value


def _extract_message_text(update: Any) -> str:
    message = _extract_message(update)
    body = None
    if isinstance(message, dict):
        body = message.get("body")
    else:
        body = getattr(message, "body", None)
    if body is None:
        return ""
    text = None
    if isinstance(body, dict):
        text = body.get("text")
    else:
        text = getattr(body, "text", None)
    if text is None:
        return ""
    return str(text)


def _extract_chat_id(update: Any) -> Optional[int]:
    direct = getattr(update, "chat_id", None)
    if isinstance(update, dict):
        direct = update.get("chat_id")
    chat_id = _to_int(direct)
    if chat_id is not None:
        return chat_id

    message = _extract_message(update)
    recipient = None
    if isinstance(message, dict):
        recipient = message.get("recipient")
    else:
        recipient = getattr(message, "recipient", None)
    if recipient is None:
        return None
    if hasattr(message, "chat"):
        chat = getattr(message, "chat")
        chat_id = _to_int(getattr(chat, "chat_id", None))
        if chat_id is not None:
            return chat_id
    if isinstance(recipient, dict):
        return _to_int(recipient.get("chat_id"))
    return _to_int(getattr(recipient, "chat_id", None))


def _extract_chat_type(update: Any) -> str:
    message = _extract_message(update)
    if message is None:
        return ""
    chat = getattr(message, "chat", None)
    if chat is not None:
        chat_type = getattr(chat, "chat_type", None)
        if chat_type is not None:
            return str(chat_type)
    recipient = None
    if isinstance(message, dict):
        recipient = message.get("recipient")
    else:
        recipient = getattr(message, "recipient", None)
    if recipient is None:
        return ""
    if isinstance(recipient, dict):
        return str(recipient.get("chat_type") or "")
    return str(getattr(recipient, "chat_type", "") or "")


def _extract_sender_id(update: Any) -> Optional[int]:
    direct = getattr(update, "user_id", None)
    if isinstance(update, dict):
        direct = update.get("user_id")
    sender_id = _to_int(direct)
    if sender_id is not None:
        return sender_id

    message = _extract_message(update)
    sender = None
    if isinstance(message, dict):
        sender = message.get("sender")
    else:
        sender = getattr(message, "sender", None)
    if sender is not None:
        if isinstance(sender, dict):
            sender_id = _to_int(sender.get("user_id"))
        else:
            sender_id = _to_int(getattr(sender, "user_id", None))
        if sender_id is not None:
            return sender_id

    user = None
    if isinstance(update, dict):
        user = update.get("user")
    else:
        user = getattr(update, "user", None)
    if user is None:
        return None
    if isinstance(user, dict):
        return _to_int(user.get("user_id"))
    return _to_int(getattr(user, "user_id", None))


def _extract_user_id(update: Any) -> Optional[int]:
    return _extract_sender_id(update)


def _extract_callback_payload(update: Any) -> Optional[str]:
    callback = _extract_callback(update)
    if callback is None:
        return None
    if isinstance(callback, dict):
        payload = callback.get("payload")
    else:
        payload = getattr(callback, "payload", None)
    if payload is None:
        return None
    return str(payload)


def _extract_start_payload(update: Any) -> Optional[str]:
    direct_start = getattr(update, "start_payload", None)
    if isinstance(update, dict):
        direct_start = update.get("start_payload")
    start_payload = _to_non_empty_str(direct_start)
    if start_payload is not None:
        return start_payload

    direct_payload = getattr(update, "payload", None)
    if isinstance(update, dict):
        direct_payload = update.get("payload")
    payload = _to_non_empty_str(direct_payload)
    if payload is not None and _extract_update_type(update) == "bot_started":
        return payload

    message = _extract_message(update)
    if message is None:
        return None
    message_start = getattr(message, "start_payload", None)
    if isinstance(message, dict):
        message_start = message.get("start_payload")
    start_from_message = _to_non_empty_str(message_start)
    if start_from_message is not None:
        return start_from_message

    text = _extract_message_text(update)
    return _parse_start_payload_from_text(text)


def _extract_chat_ref(update: Any) -> Any:
    chat_id = _extract_chat_id(update)
    chat_type = _extract_chat_type(update)
    if chat_id is None and not chat_type:
        return _MISSING
    return {"id": chat_id, "type": chat_type}


def _extract_sender_ref(update: Any) -> Any:
    sender_id = _extract_sender_id(update)
    if sender_id is None:
        return _MISSING
    return {"id": sender_id}


def _extract_user_ref(update: Any) -> Any:
    user_id = _extract_user_id(update)
    if user_id is None:
        return _MISSING
    return {"id": user_id}


def _extract_content_type(update: Any) -> Any:
    attachments = _extract_message_attachments(update)
    if attachments:
        attachment_type = _extract_attachment_type(attachments[0])
        if attachment_type is not None:
            return attachment_type.value
    if _extract_message_text(update).strip():
        return "text"
    return _MISSING


def _extract_command_parts(update: Any) -> Tuple[Optional[str], Optional[str]]:
    text = _extract_message_text(update).strip()
    if not text.startswith("/"):
        return None, None
    parts = text.split(None, 1)
    command_token = parts[0][1:]
    if not command_token:
        return None, None
    if "@" in command_token:
        command_token = command_token.split("@", 1)[0]
    command_name = command_token.strip().lower()
    if not command_name:
        return None, None
    if len(parts) < 2:
        return command_name, None
    args = parts[1].strip()
    if not args:
        return command_name, None
    return command_name, args


def _extract_command_name(update: Any) -> Any:
    command_name, _ = _extract_command_parts(update)
    if command_name is None:
        return _MISSING
    return command_name


def _extract_command_args(update: Any) -> Any:
    _, args = _extract_command_parts(update)
    if args is None:
        return _MISSING
    return args


def _has_attachment(update: Any, attachment_type: AttachmentType) -> bool:
    for attachment in _extract_message_attachments(update):
        if _extract_attachment_type(attachment) == attachment_type:
            return True
    return False


def _parse_start_payload_from_text(text: str) -> Optional[str]:
    normalized = str(text or "").strip()
    if not normalized:
        return None

    parts = normalized.split(None, 1)
    command = parts[0]
    if command != "/start" and not command.startswith("/start@"):
        return None
    if len(parts) < 2:
        return None

    payload = parts[1].strip()
    if not payload:
        return None
    return payload


def _to_non_empty_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _to_attachment_type(value: Any) -> Optional[AttachmentType]:
    if isinstance(value, AttachmentType):
        return value
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    try:
        return AttachmentType(raw)
    except ValueError:
        return None


def _to_int(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


_ROOT_EXTRACTORS: Dict[str, Callable[[Any], Any]] = {
    "update_type": _extract_update_type,
    "chat_id": _extract_chat_id,
    "chat_type": _extract_chat_type,
    "sender_id": _extract_sender_id,
    "user_id": _extract_user_id,
    "text": _extract_message_text,
    "data": _extract_callback_payload,
    "callback_data": _extract_callback_payload,
    "callback_payload": _extract_callback_payload,
    "start_payload": _extract_start_payload,
    "chat": _extract_chat_ref,
    "sender": _extract_sender_ref,
    "from_user": _extract_user_ref,
    "user": _extract_user_ref,
    "message": _extract_message,
    "callback": _extract_callback,
    "content_type": _extract_content_type,
    "command": _extract_command_name,
    "command_name": _extract_command_name,
    "command_args": _extract_command_args,
    "args": _extract_command_args,
    "image": lambda update: _has_attachment(update, AttachmentType.IMAGE),
    "video": lambda update: _has_attachment(update, AttachmentType.VIDEO),
    "audio": lambda update: _has_attachment(update, AttachmentType.AUDIO),
    "file": lambda update: _has_attachment(update, AttachmentType.FILE),
    "sticker": lambda update: _has_attachment(update, AttachmentType.STICKER),
    "contact": lambda update: _has_attachment(update, AttachmentType.CONTACT),
    "inline_keyboard": lambda update: _has_attachment(update, AttachmentType.INLINE_KEYBOARD),
    "share": lambda update: _has_attachment(update, AttachmentType.SHARE),
    "location": lambda update: _has_attachment(update, AttachmentType.LOCATION),
}

