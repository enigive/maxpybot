from __future__ import annotations

from typing import Any, Dict


def ensure_raw_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result["raw_payload"] = dict(payload)
    return result


def normalize_unknown_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keeps payload untouched but centralizes compat hook."""

    return payload


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_unknown_fields(payload)
    return ensure_raw_payload(normalized)
