from __future__ import annotations

from typing import Any, Dict, Optional

from .storage import BaseStorage, StorageKey


class FSMContext:
    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self._storage = storage
        self._key = key

    @property
    def key(self) -> StorageKey:
        return self._key

    async def get_state(self) -> Optional[str]:
        return await self._storage.get_state(self._key)

    async def set_state(self, state: Optional[str]) -> None:
        await self._storage.set_state(self._key, state)

    async def get_data(self) -> Dict[str, Any]:
        return await self._storage.get_data(self._key)

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self._storage.set_data(self._key, data)

    async def update_data(self, data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return await self._storage.update_data(self._key, data=data, **kwargs)

    async def clear(self) -> None:
        await self._storage.clear(self._key)


def create_fsm_context(storage: BaseStorage, chat_id: Any, user_id: Any) -> FSMContext:
    return FSMContext(storage=storage, key=StorageKey.build(chat_id=chat_id, user_id=user_id))


def create_fsm_context_from_update(storage: BaseStorage, update: Any) -> Optional[FSMContext]:
    key = resolve_storage_key_from_update(update)
    if key is None:
        return None
    return FSMContext(storage=storage, key=key)


def resolve_storage_key_from_update(update: Any) -> Optional[StorageKey]:
    update_dict = _as_dict(update)
    chat_id = _first_non_none(
        update_dict.get("chat_id"),
        _extract_nested(update_dict, "message", "recipient", "chat_id"),
        _extract_nested(update_dict, "chat", "chat_id"),
    )
    user_id = _first_non_none(
        update_dict.get("user_id"),
        _extract_nested(update_dict, "user", "user_id"),
        _extract_nested(update_dict, "message", "sender", "user_id"),
        _extract_nested(update_dict, "callback", "user", "user_id"),
    )

    if chat_id is None or user_id is None:
        return None
    try:
        return StorageKey.build(chat_id=chat_id, user_id=user_id)
    except (TypeError, ValueError):
        return None


def _extract_nested(value: Dict[str, Any], *path: str) -> Any:
    current: Any = value
    for part in path:
        current_dict = _as_dict(current)
        if not current_dict:
            return None
        current = current_dict.get(part)
    return current


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(by_alias=True)
        if isinstance(dumped, dict):
            return dumped
    return {}


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None
