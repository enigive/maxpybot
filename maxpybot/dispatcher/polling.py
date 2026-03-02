from __future__ import annotations

from typing import List, Optional

from ..api_client import MaxBotAPI
from .router import Router


class PollingRunner:
    def __init__(self, api: MaxBotAPI, router: Router) -> None:
        self._api = api
        self._router = router
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def run(self, marker: Optional[int] = None, types: Optional[List[str]] = None) -> None:
        self._running = True
        try:
            async for update in self._api.iter_updates(marker=marker, types=types):
                await self._router.dispatch(update)
        finally:
            self._running = False
