from __future__ import annotations

import importlib
import inspect
import json
from typing import Any, Dict, Optional

from .storage import BaseStorage, StorageKey


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis_client: Any,
        key_prefix: str = "maxpybot:fsm",
        state_ttl_seconds: Optional[int] = None,
        data_ttl_seconds: Optional[int] = None,
    ) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._state_ttl = state_ttl_seconds
        self._data_ttl = data_ttl_seconds

    @classmethod
    def from_url(
        cls,
        url: str,
        key_prefix: str = "maxpybot:fsm",
        state_ttl_seconds: Optional[int] = None,
        data_ttl_seconds: Optional[int] = None,
    ) -> "RedisStorage":
        try:
            redis_asyncio = importlib.import_module("redis.asyncio")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("RedisStorage requires 'redis' package. Install it with: pip install redis") from exc

        redis_client = redis_asyncio.from_url(url, decode_responses=True)
        return cls(
            redis_client=redis_client,
            key_prefix=key_prefix,
            state_ttl_seconds=state_ttl_seconds,
            data_ttl_seconds=data_ttl_seconds,
        )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        raw = await self._redis.get(self._state_key(key))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)

    async def set_state(self, key: StorageKey, state: Optional[str]) -> None:
        redis_key = self._state_key(key)
        if state is None:
            await self._redis.delete(redis_key)
            return
        await self._redis.set(redis_key, str(state))
        await self._set_expire(redis_key, self._state_ttl)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        raw = await self._redis.get(self._data_key(key))
        if raw is None:
            return {}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            value = json.loads(str(raw))
        except Exception:  # noqa: BLE001
            return {}
        if isinstance(value, dict):
            return value
        return {}

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        redis_key = self._data_key(key)
        payload = json.dumps(data)
        await self._redis.set(redis_key, payload)
        await self._set_expire(redis_key, self._data_ttl)

    async def clear(self, key: StorageKey) -> None:
        await self._redis.delete(self._state_key(key), self._data_key(key))

    async def close(self) -> None:
        close_method = getattr(self._redis, "aclose", None)
        if close_method is None:
            close_method = getattr(self._redis, "close", None)
        if close_method is None:
            return
        result = close_method()
        if inspect.isawaitable(result):
            await result

    async def _set_expire(self, redis_key: str, ttl: Optional[int]) -> None:
        if ttl is None:
            return
        await self._redis.expire(redis_key, int(ttl))

    def _state_key(self, key: StorageKey) -> str:
        return "{0}:{1}:state".format(self._key_prefix, key.as_token())

    def _data_key(self, key: StorageKey) -> str:
        return "{0}:{1}:data".format(self._key_prefix, key.as_token())
