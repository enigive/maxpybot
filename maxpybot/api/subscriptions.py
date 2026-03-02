from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..types import SubscriptionSchema, build_request_payload
from .base import BaseAPIGroup


class SubscriptionsAPI(BaseAPIGroup):
    async def get_subscriptions(self) -> Any:
        return await self._request_model("GetSubscriptionsResult", "GET", "subscriptions")

    async def subscribe(
        self,
        subscribe_url: str,
        update_types: Optional[List[str]] = None,
        secret: str = "",
    ) -> Any:
        payload = build_request_payload(
            {
                "url": subscribe_url,
                "update_types": update_types or [],
                "secret": secret,
                "version": self._transport.version,
            },
            SubscriptionSchema,
        )
        return await self._request_model("SimpleQueryResult", "POST", "subscriptions", json_body=payload)

    async def unsubscribe(self, subscription_url: str) -> Any:
        return await self._request_model(
            "SimpleQueryResult",
            "DELETE",
            "subscriptions",
            params={"url": subscription_url},
        )

    async def unsubscribe_all(self) -> List[Any]:
        subscriptions_response = await self.get_subscriptions()
        subscriptions = _extract_subscriptions(subscriptions_response)

        results: List[Any] = []
        for item in subscriptions:
            url = _extract_subscription_url(item)
            if not url:
                continue
            results.append(await self.unsubscribe(url))
        return results

    # OpenAPI parity aliases (operationId)
    getSubscriptions = get_subscriptions
    unsubscribeAll = unsubscribe_all


def _extract_subscriptions(value: Any) -> List[Any]:
    if isinstance(value, dict):
        raw = value.get("subscriptions")
        if isinstance(raw, list):
            return raw
        return []
    if hasattr(value, "subscriptions"):
        items = getattr(value, "subscriptions")
        if isinstance(items, list):
            return items
    return []


def _extract_subscription_url(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("url") or "")
    if hasattr(value, "url"):
        return str(getattr(value, "url") or "")
    return ""
