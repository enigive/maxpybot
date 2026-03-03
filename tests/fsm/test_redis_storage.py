from typing import Any, Dict, List, Optional, Tuple

import pytest

from maxpybot.fsm import RedisStorage, StorageKey


class FakeRedisClient:
    def __init__(self) -> None:
        self.values: Dict[str, Any] = {}
        self.expire_calls: List[Tuple[str, int]] = []
        self.closed = False

    async def get(self, key: str) -> Any:
        return self.values.get(key)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self.values.pop(key, None)

    async def expire(self, key: str, ttl: int) -> None:
        self.expire_calls.append((key, ttl))

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_redis_storage_state_and_data_roundtrip() -> None:
    redis = FakeRedisClient()
    storage = RedisStorage(redis_client=redis, key_prefix="test", state_ttl_seconds=10, data_ttl_seconds=20)
    key = StorageKey(chat_id=10, user_id=20)

    await storage.set_state(key, "awaiting_phone")
    await storage.set_data(key, {"step": 1})

    assert await storage.get_state(key) == "awaiting_phone"
    assert await storage.get_data(key) == {"step": 1}

    updated = await storage.update_data(key, {"name": "Alice"}, done=False)
    assert updated == {"step": 1, "name": "Alice", "done": False}
    assert await storage.get_data(key) == {"step": 1, "name": "Alice", "done": False}

    assert ("test:10:20:state", 10) in redis.expire_calls
    assert ("test:10:20:data", 20) in redis.expire_calls

    await storage.clear(key)
    assert await storage.get_state(key) is None
    assert await storage.get_data(key) == {}


@pytest.mark.asyncio
async def test_redis_storage_invalid_json_fallback() -> None:
    redis = FakeRedisClient()
    storage = RedisStorage(redis_client=redis)
    key = StorageKey(chat_id=1, user_id=2)
    redis.values["maxpybot:fsm:1:2:data"] = "not-json"

    assert await storage.get_data(key) == {}


@pytest.mark.asyncio
async def test_redis_storage_close_calls_client() -> None:
    redis = FakeRedisClient()
    storage = RedisStorage(redis_client=redis)

    await storage.close()
    assert redis.closed is True


def test_redis_storage_from_url_without_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_import_module(name: str) -> Any:
        raise ImportError("missing redis package")

    monkeypatch.setattr("maxpybot.fsm.redis.importlib.import_module", fake_import_module)

    with pytest.raises(RuntimeError, match="requires 'redis'"):
        RedisStorage.from_url("redis://localhost:6379/0")


def test_redis_storage_from_url_with_mocked_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Optional[Any]] = {"url": None, "decode_responses": None}

    class FakeRedisAsyncioModule:
        @staticmethod
        def from_url(url: str, decode_responses: bool = False) -> FakeRedisClient:
            captured["url"] = url
            captured["decode_responses"] = decode_responses
            return FakeRedisClient()

    def fake_import_module(name: str) -> Any:
        return FakeRedisAsyncioModule

    monkeypatch.setattr("maxpybot.fsm.redis.importlib.import_module", fake_import_module)

    storage = RedisStorage.from_url("redis://localhost:6379/1", key_prefix="pref")
    key = StorageKey(chat_id=5, user_id=6)
    assert storage._state_key(key) == "pref:5:6:state"  # noqa: SLF001
    assert captured["url"] == "redis://localhost:6379/1"
    assert captured["decode_responses"] is True
