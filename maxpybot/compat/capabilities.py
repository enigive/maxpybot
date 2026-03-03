from __future__ import annotations

from typing import Any, Dict, List, Tuple

CAP_DIALOG_LEGACY_IDS = "dialog_legacy_ids"
CAP_DIALOG_FLAT_IDS = "dialog_flat_ids"
CAP_DIALOG_NESTED_DIALOG = "dialog_nested_dialog"
CAP_DIALOG_NESTED_USER = "dialog_nested_user"
CAP_DIALOG_USER_LOCALE = "dialog_user_locale"
CAP_BOT_STOPPED_PAYLOAD = "bot_stopped_payload"

DIALOG_UPDATE_TYPES: Tuple[str, ...] = (
    "dialog_muted",
    "dialog_unmuted",
    "dialog_cleared",
    "dialog_removed",
)

CAPABILITY_MATRIX: Dict[str, Tuple[str, ...]] = {
    "bot_stopped": (
        CAP_DIALOG_LEGACY_IDS,
        CAP_DIALOG_FLAT_IDS,
        CAP_DIALOG_NESTED_DIALOG,
        CAP_DIALOG_NESTED_USER,
        CAP_DIALOG_USER_LOCALE,
        CAP_BOT_STOPPED_PAYLOAD,
    ),
    "dialog_muted": (
        CAP_DIALOG_LEGACY_IDS,
        CAP_DIALOG_FLAT_IDS,
        CAP_DIALOG_NESTED_DIALOG,
        CAP_DIALOG_NESTED_USER,
        CAP_DIALOG_USER_LOCALE,
    ),
    "dialog_unmuted": (
        CAP_DIALOG_LEGACY_IDS,
        CAP_DIALOG_FLAT_IDS,
        CAP_DIALOG_NESTED_DIALOG,
        CAP_DIALOG_NESTED_USER,
        CAP_DIALOG_USER_LOCALE,
    ),
    "dialog_cleared": (
        CAP_DIALOG_LEGACY_IDS,
        CAP_DIALOG_FLAT_IDS,
        CAP_DIALOG_NESTED_DIALOG,
        CAP_DIALOG_NESTED_USER,
        CAP_DIALOG_USER_LOCALE,
    ),
    "dialog_removed": (
        CAP_DIALOG_LEGACY_IDS,
        CAP_DIALOG_FLAT_IDS,
        CAP_DIALOG_NESTED_DIALOG,
        CAP_DIALOG_NESTED_USER,
        CAP_DIALOG_USER_LOCALE,
    ),
}


def supported_capabilities(update_type: str) -> Tuple[str, ...]:
    return CAPABILITY_MATRIX.get(update_type, tuple())


def detect_payload_capabilities(update_type: str, payload: Dict[str, Any]) -> List[str]:
    if update_type not in CAPABILITY_MATRIX:
        return []
    detected: List[str] = []

    if "dialog_id" in payload or "chatId" in payload or "userId" in payload:
        _append_unique(detected, CAP_DIALOG_LEGACY_IDS)
    if "chat_id" in payload or "user_id" in payload:
        _append_unique(detected, CAP_DIALOG_FLAT_IDS)

    dialog_value = payload.get("dialog")
    if isinstance(dialog_value, dict):
        _append_unique(detected, CAP_DIALOG_NESTED_DIALOG)
    user_value = payload.get("user")
    if isinstance(user_value, dict):
        _append_unique(detected, CAP_DIALOG_NESTED_USER)
    if payload.get("user_locale") is not None:
        _append_unique(detected, CAP_DIALOG_USER_LOCALE)

    if update_type == "bot_stopped" and "payload" in payload:
        _append_unique(detected, CAP_BOT_STOPPED_PAYLOAD)

    return detected


def _append_unique(values: List[str], value: str) -> None:
    if value not in values:
        values.append(value)
