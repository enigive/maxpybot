from __future__ import annotations

from typing import Any, Dict

from .base import BaseAPIGroup


class BotsAPI(BaseAPIGroup):
    async def get_my_info(self) -> Any:
        return await self._request_model("BotInfo", "GET", "me")

    async def edit_my_info(self, patch: Dict[str, Any]) -> Any:
        return await self._request_model("BotInfo", "PATCH", "me", json_body=patch)

    # OpenAPI parity aliases (operationId)
    getMyInfo = get_my_info
    editMyInfo = edit_my_info
