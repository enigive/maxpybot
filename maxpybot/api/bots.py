from __future__ import annotations

from typing import Any, Dict, Union

from ..types import BotPatchSchema, build_request_payload
from .base import BaseAPIGroup


class BotsAPI(BaseAPIGroup):
    async def get_my_info(self) -> Any:
        return await self._request_model("BotInfo", "GET", "me")

    async def edit_my_info(self, patch: Union[Dict[str, Any], BotPatchSchema]) -> Any:
        body = build_request_payload(patch, BotPatchSchema)
        return await self._request_model("BotInfo", "PATCH", "me", json_body=body)

    # OpenAPI parity aliases (operationId)
    getMyInfo = get_my_info
    editMyInfo = edit_my_info
