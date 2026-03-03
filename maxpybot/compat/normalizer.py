from __future__ import annotations

import warnings
from typing import Any, Dict

from .capabilities import DIALOG_UPDATE_TYPES

_DIALOG_LIFECYCLE_TYPES = DIALOG_UPDATE_TYPES + ("bot_stopped",)


def ensure_raw_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result["raw_payload"] = payload.get("raw_payload", dict(payload))
    return result


def normalize_unknown_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keeps payload untouched but centralizes compat hook."""

    return _normalize_dialog_lifecycle_fields(payload)


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_payload = dict(payload)
    normalized = normalize_unknown_fields(dict(payload))
    normalized["raw_payload"] = raw_payload
    return ensure_raw_payload(normalized)


def _normalize_dialog_lifecycle_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    update_type = str(payload.get("update_type") or "")
    if update_type not in _DIALOG_LIFECYCLE_TYPES:
        return payload

    result = dict(payload)

    _apply_alias(
        result,
        update_type=update_type,
        old_field="dialog_id",
        new_field="chat_id",
    )
    _apply_alias(
        result,
        update_type=update_type,
        old_field="chatId",
        new_field="chat_id",
    )
    _apply_alias(
        result,
        update_type=update_type,
        old_field="userId",
        new_field="user_id",
    )

    dialog = result.get("dialog")
    if isinstance(dialog, dict):
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.chat_id",
            source_key="chat_id",
            new_field="chat_id",
            warn_deprecated=False,
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.dialog_id",
            source_key="dialog_id",
            new_field="chat_id",
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.chatId",
            source_key="chatId",
            new_field="chat_id",
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.id",
            source_key="id",
            new_field="chat_id",
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.user_id",
            source_key="user_id",
            new_field="user_id",
            warn_deprecated=False,
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.with_user_id",
            source_key="with_user_id",
            new_field="user_id",
        )
        _apply_nested_alias(
            result,
            source=dialog,
            update_type=update_type,
            old_field="dialog.userId",
            source_key="userId",
            new_field="user_id",
        )

    user_value = result.get("user")
    if isinstance(user_value, dict):
        _apply_nested_alias(
            result,
            source=user_value,
            update_type=update_type,
            old_field="user.user_id",
            source_key="user_id",
            new_field="user_id",
            warn_deprecated=False,
        )
        _apply_nested_alias(
            result,
            source=user_value,
            update_type=update_type,
            old_field="user.userId",
            source_key="userId",
            new_field="user_id",
        )

    return result


def _apply_alias(result: Dict[str, Any], update_type: str, old_field: str, new_field: str) -> None:
    if new_field in result or old_field not in result:
        return
    result[new_field] = result[old_field]
    _warn_deprecated_field(update_type, old_field, new_field)


def _apply_nested_alias(
    result: Dict[str, Any],
    source: Dict[str, Any],
    update_type: str,
    old_field: str,
    source_key: str,
    new_field: str,
    warn_deprecated: bool = True,
) -> None:
    if new_field in result or source_key not in source:
        return
    result[new_field] = source[source_key]
    if warn_deprecated:
        _warn_deprecated_field(update_type, old_field, new_field)


def _warn_deprecated_field(update_type: str, old_field: str, new_field: str) -> None:
    warnings.warn(
        "{0}: field '{1}' is deprecated, use '{2}'".format(update_type, old_field, new_field),
        category=DeprecationWarning,
        stacklevel=3,
    )
