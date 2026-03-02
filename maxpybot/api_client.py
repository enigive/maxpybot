from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .api.bots import BotsAPI
from .api.chats import ChatsAPI
from .api.messages import MessagesAPI
from .api.subscriptions import SubscriptionsAPI
from .api.uploads import UploadsAPI
from .compat.update_parser import UpdateParser
from .constants import (
    DEFAULT_API_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLL_PAUSE_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_UPDATES_LIMIT,
    DEFAULT_VERSION,
)
from .exceptions import EmptyTokenError, TimeoutError
from .transport.client import TransportClient

UpdateHandler = Callable[[Any], None]


class MaxBotAPI:
    """Main API client entrypoint."""

    def __init__(
        self,
        token: str,
        base_url: str = DEFAULT_API_URL,
        version: str = DEFAULT_VERSION,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        pause_seconds: int = DEFAULT_POLL_PAUSE_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        debug: bool = False,
        update_handler: Optional[UpdateHandler] = None,
        session: Any = None,
    ) -> None:
        if not token:
            raise EmptyTokenError("bot token is empty")

        self._transport = TransportClient(
            token=token,
            base_url=base_url,
            version=version,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            session=session,
        )
        self._update_parser = UpdateParser(debug=debug)

        self.pause_seconds = pause_seconds
        self.timeout_seconds = timeout_seconds
        self.max_updates_limit = DEFAULT_UPDATES_LIMIT
        self.max_retries = max_retries
        self.update_handler = update_handler

        self.bots = BotsAPI(self._transport)
        self.chats = ChatsAPI(self._transport)
        self.messages = MessagesAPI(self._transport)
        self.subscriptions = SubscriptionsAPI(self._transport)
        self.uploads = UploadsAPI(self._transport)

        # Go-like aliases
        self.Bots = self.bots
        self.Chats = self.chats
        self.Messages = self.messages
        self.Subscriptions = self.subscriptions
        self.Uploads = self.uploads

    async def __aenter__(self) -> "MaxBotAPI":
        await self._transport.open()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()

    def get_errors(self) -> "asyncio.Queue[Exception]":
        return self._transport.errors()

    async def get_updates(
        self,
        marker: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        limit: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if marker is not None:
            params["marker"] = str(marker)
        if timeout_seconds is not None:
            params["timeout"] = str(timeout_seconds)
        if limit is not None:
            params["limit"] = str(limit)
        if types:
            params["types"] = types

        try:
            return await self._transport.request_json(
                "GET",
                "updates",
                params=params,
                retry_attempts=self.max_retries,
            )
        except TimeoutError:
            # Mirror Go behavior: timeout during long polling is treated as empty page.
            return {"updates": [], "marker": marker}

    async def iter_updates(
        self,
        marker: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> AsyncIterator[Any]:
        next_marker = marker
        while True:
            response = await self.get_updates(
                marker=next_marker,
                timeout_seconds=self.timeout_seconds,
                limit=self.max_updates_limit,
                types=types,
            )
            raw_updates = response.get("updates", [])
            for raw_update in raw_updates:
                update = self._update_parser.parse_update(raw_update)
                if self.update_handler is not None:
                    self.update_handler(update)
                else:
                    yield update

            if response.get("marker") is not None:
                next_marker = response["marker"]

            if not raw_updates:
                await asyncio.sleep(self.pause_seconds)

    getUpdates = get_updates
    iterUpdates = iter_updates
