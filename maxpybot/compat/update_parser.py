from __future__ import annotations

from typing import Any, Dict

from ..types.generated.runtime import validate_with_model
from .attachments import normalize_message_attachments
from .normalizer import normalize_payload


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
    # Backward-compatible aliases observed in previous MAX API payloads.
    "bot_stopped": "Update",
    "dialog_muted": "Update",
    "dialog_unmuted": "Update",
    "dialog_removed": "Update",
    "dialog_cleared": "Update",
}


class UpdateParser:
    def __init__(self, debug: bool = False) -> None:
        self._debug = debug

    def parse_update(self, raw_update: Dict[str, Any]) -> Any:
        normalized = normalize_payload(dict(raw_update))
        update_type = str(normalized.get("update_type") or "")

        # Process message attachments before model validation.
        if update_type in ("message_created", "message_edited", "message_callback", "message_chat_created"):
            message = normalized.get("message")
            if isinstance(message, dict):
                normalized["message"] = normalize_message_attachments(message)

        if self._debug:
            normalized["debug_raw"] = raw_update

        model_name = UPDATE_MODEL_BY_TYPE.get(update_type)
        if not model_name:
            return normalized
        return validate_with_model(model_name, normalized)
