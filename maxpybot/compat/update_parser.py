from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from ..types.generated.runtime import get_model_class, validate_with_model
from .attachments import normalize_message_attachments
from .capabilities import detect_payload_capabilities, supported_capabilities
from .normalizer import normalize_payload

if TYPE_CHECKING:
    from ..api_client import MaxBot
    from ..types.base import MaxBaseModel


KNOWN_UPDATE_TYPES = (
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
)


UPDATE_MODEL_BY_TYPE = {
    "message_callback": "MessageCallbackUpdate",
    "message_created": "MessageCreatedUpdate",
    "message_removed": "MessageRemovedUpdate",
    "message_edited": "MessageEditedUpdate",
    "bot_added": "BotAddedToChatUpdate",
    "bot_removed": "BotRemovedFromChatUpdate",
    "user_added": "UserAddedToChatUpdate",
    "user_removed": "UserRemovedFromChatUpdate",
    "bot_started": "BotStartedUpdate",
    "chat_title_changed": "ChatTitleChangedUpdate",
    "message_chat_created": "MessageChatCreatedUpdate",
    "bot_stopped": "BotStoppedUpdate",
    "dialog_muted": "DialogMutedUpdate",
    "dialog_unmuted": "DialogUnmutedUpdate",
    "dialog_removed": "DialogRemovedUpdate",
    "dialog_cleared": "DialogClearedUpdate",
}


class UpdateParser:
    def __init__(self, debug: bool = False) -> None:
        self._debug = debug

    def parse_update(self, raw_update: Dict[str, Any], bot: Optional[MaxBot] = None) -> Any:
        normalized = normalize_payload(dict(raw_update))
        update_type = str(normalized.get("update_type") or "")

        # Process message attachments before model validation.
        if update_type in ("message_created", "message_edited", "message_callback", "message_chat_created"):
            message = normalized.get("message")
            if isinstance(message, dict):
                normalized["message"] = normalize_message_attachments(message)

        if self._debug:
            normalized["debug_raw"] = raw_update

        capabilities = detect_payload_capabilities(update_type, normalized)
        if capabilities:
            normalized["compat_capabilities"] = capabilities
        supported = supported_capabilities(update_type)
        if supported:
            normalized["compat_supported_capabilities"] = list(supported)

        model_name = UPDATE_MODEL_BY_TYPE.get(update_type)
        if not model_name:
            return _build_unknown_update(
                normalized,
                "unsupported update_type: {0}".format(update_type or "<empty>"),
            )

        parsed, parse_error = _parse_with_model(model_name, normalized)
        if parsed is None:
            return _build_unknown_update(normalized, parse_error or "validation failed")

        if update_type == "message_callback":
            _bind_callback_message(parsed)

        if bot is not None:
            _inject_bot(parsed, bot)

        return parsed


def _parse_with_model(model_name: str, payload: Dict[str, Any]) -> Any:
    klass = get_model_class(model_name)
    if klass is None:
        return None, "model not found: {0}".format(model_name)
    try:
        return klass.model_validate(payload), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def _build_unknown_update(payload: Dict[str, Any], parse_error: str) -> Any:
    unknown_payload = dict(payload)
    unknown_payload["parse_error"] = parse_error
    return validate_with_model("UnknownUpdate", unknown_payload)


def _bind_callback_message(update: Any) -> None:
    callback = getattr(update, "callback", None)
    message = getattr(update, "message", None)
    if callback is None:
        return
    if getattr(callback, "message", None) is not None:
        return
    try:
        callback.message = message
    except Exception:  # noqa: BLE001
        return


def _inject_bot(obj: Any, bot: MaxBot) -> None:
    from ..types.base import MaxBaseModel

    if isinstance(obj, MaxBaseModel):
        obj.bot = bot
        # Recursively inject into fields
        for field_name in obj.__class__.model_fields:
            value = getattr(obj, field_name, None)
            _inject_bot(value, bot)
    elif isinstance(obj, list):
        for item in obj:
            _inject_bot(item, bot)
    elif isinstance(obj, dict):
        for item in obj.values():
            _inject_bot(item, bot)
    elif hasattr(obj, "__dict__"):
        # For non-pydantic objects that might contain pydantic objects
        for value in obj.__dict__.values():
            _inject_bot(value, bot)
