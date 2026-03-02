from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..transport.client import TransportClient
from ..types.generated.runtime import validate_with_model


class BaseAPIGroup:
    def __init__(self, transport: TransportClient) -> None:
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Tuple[int, ...] = (200,),
    ) -> Dict[str, Any]:
        return await self._transport.request_json(
            method=method,
            path=path,
            params=params,
            json_body=json_body,
            authorized=authorized,
            expected_statuses=expected_statuses,
        )

    async def _request_model(
        self,
        model_name: str,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Tuple[int, ...] = (200,),
    ) -> Any:
        payload = await self._request(
            method=method,
            path=path,
            params=params,
            json_body=json_body,
            authorized=authorized,
            expected_statuses=expected_statuses,
        )
        return validate_with_model(model_name, payload)
