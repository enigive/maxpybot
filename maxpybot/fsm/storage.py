from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class StorageKey:
    chat_id: int
    user_id: int

    @classmethod
    def build(cls, chat_id: Any, user_id: Any) -> "StorageKey":
        return cls(chat_id=int(chat_id), user_id=int(user_id))

    def as_token(self) -> str:
        return "{0}:{1}".format(self.chat_id, self.user_id)


class BaseStorage(ABC):
    @abstractmethod
    async def get_state(self, key: StorageKey) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def set_state(self, key: StorageKey, state: Optional[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def update_data(
        self,
        key: StorageKey,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        current = await self.get_data(key)
        if data:
            current.update(dict(data))
        if kwargs:
            current.update(kwargs)
        await self.set_data(key, current)
        return current

    @abstractmethod
    async def clear(self, key: StorageKey) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
