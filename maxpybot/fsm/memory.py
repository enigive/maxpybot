from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .storage import BaseStorage, StorageKey


class MemoryStorage(BaseStorage):
    def __init__(self) -> None:
        self._states: Dict[str, str] = {}
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        token = key.as_token()
        async with self._lock:
            return self._states.get(token)

    async def set_state(self, key: StorageKey, state: Optional[str]) -> None:
        token = key.as_token()
        async with self._lock:
            if state is None:
                self._states.pop(token, None)
                return
            self._states[token] = str(state)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        token = key.as_token()
        async with self._lock:
            return dict(self._data.get(token, {}))

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        token = key.as_token()
        async with self._lock:
            self._data[token] = dict(data)

    async def clear(self, key: StorageKey) -> None:
        token = key.as_token()
        async with self._lock:
            self._states.pop(token, None)
            self._data.pop(token, None)

    async def close(self) -> None:
        return None
