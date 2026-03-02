from __future__ import annotations

from typing import Any, Dict, Type, TypeVar, Union

from pydantic import BaseModel

from .base import MaxBaseModel

SchemaModelT = TypeVar("SchemaModelT", bound=MaxBaseModel)


def build_request_payload(
    payload: Union[Dict[str, Any], BaseModel],
    schema: Type[SchemaModelT],
) -> Dict[str, Any]:
    """Normalize dict/model input into a validated request payload."""

    if isinstance(payload, BaseModel):
        raw_payload = payload.model_dump(by_alias=True, exclude_none=True)
    else:
        raw_payload = payload

    normalized = schema.model_validate(raw_payload)
    return normalized.model_dump(by_alias=True, exclude_none=True)
