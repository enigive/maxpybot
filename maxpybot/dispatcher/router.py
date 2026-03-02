from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List, Optional

FilterCallable = Callable[[Any], Any]
HandlerCallable = Callable[[Any], Awaitable[Any]]


@dataclass
class _HandlerRecord:
    callback: HandlerCallable
    update_type: Optional[str]
    filters: List[FilterCallable]


class Router:
    def __init__(self) -> None:
        self._handlers: List[_HandlerRecord] = []
        self._children: List["Router"] = []

    def include_router(self, router: "Router") -> None:
        self._children.append(router)

    def register(
        self,
        callback: HandlerCallable,
        update_type: Optional[str] = None,
        filters: Optional[List[FilterCallable]] = None,
    ) -> HandlerCallable:
        self._handlers.append(_HandlerRecord(callback=callback, update_type=update_type, filters=filters or []))
        return callback

    def on_update(self, update_type: Optional[str] = None, *filters: FilterCallable) -> Callable[[HandlerCallable], HandlerCallable]:
        def _decorator(callback: HandlerCallable) -> HandlerCallable:
            self.register(callback, update_type=update_type, filters=list(filters))
            return callback

        return _decorator

    def message(self, *filters: FilterCallable) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_created", *filters)

    def callback_query(self, *filters: FilterCallable) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_callback", *filters)

    async def dispatch(self, update: Any) -> bool:
        handled = False
        for handler in self._handlers:
            if not _match_update_type(update, handler.update_type):
                continue
            if not await _passes_filters(update, handler.filters):
                continue
            await handler.callback(update)
            handled = True

        for child in self._children:
            child_handled = await child.dispatch(update)
            handled = handled or child_handled

        return handled


def _extract_update_type(update: Any) -> Optional[str]:
    if isinstance(update, dict):
        value = update.get("update_type")
    else:
        value = getattr(update, "update_type", None)
    if value is None:
        return None
    return str(value)


def _match_update_type(update: Any, expected: Optional[str]) -> bool:
    if expected is None:
        return True
    return _extract_update_type(update) == expected


async def _passes_filters(update: Any, filters: List[FilterCallable]) -> bool:
    for filter_func in filters:
        result = filter_func(update)
        if inspect.isawaitable(result):
            result = await result
        if not bool(result):
            return False
    return True
