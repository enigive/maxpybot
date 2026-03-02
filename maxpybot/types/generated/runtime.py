from __future__ import annotations

import importlib
from typing import Any, Optional, Type

from pydantic import BaseModel


def get_model_class(model_name: str) -> Optional[Type[BaseModel]]:
    try:
        module = importlib.import_module("maxpybot.types.generated.models")
    except Exception:  # noqa: BLE001
        return None
    klass = getattr(module, model_name, None)
    if isinstance(klass, type) and issubclass(klass, BaseModel):
        return klass
    return None


def validate_with_model(model_name: str, payload: Any) -> Any:
    klass = get_model_class(model_name)
    if klass is None:
        return payload
    try:
        return klass.model_validate(payload)
    except Exception:  # noqa: BLE001
        return payload
